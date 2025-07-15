"""
Performance Analytics Module

READ-ONLY performance analysis and monitoring for BMW vehicles.
Calculates 0-60 times, G-forces, power estimation, and track session data
using only OBD2 sensor data without any ECU modifications.
"""

import time
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque
import threading


@dataclass
class AccelerationEvent:
    """Represents an acceleration event (0-60, quarter-mile, etc.)"""
    start_time: datetime
    end_time: Optional[datetime] = None
    start_speed: float = 0.0  # mph
    end_speed: float = 0.0    # mph
    max_speed: float = 0.0
    max_g_force: float = 0.0
    distance: float = 0.0     # feet
    completed: bool = False
    event_type: str = "0-60"  # "0-60", "quarter-mile", "custom"


@dataclass
class PerformanceSession:
    """Represents a track/performance session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    max_speed: float = 0.0
    max_g_force: float = 0.0
    max_power_estimate: float = 0.0
    avg_boost_pressure: float = 0.0
    fuel_consumed: float = 0.0
    session_type: str = "track"  # "track", "drag", "street"
    telemetry_points: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.telemetry_points is None:
            self.telemetry_points = []


class PerformanceAnalytics:
    """
    Performance analytics engine for BMW vehicles
    
    Provides advanced performance monitoring including:
    - 0-60 mph acceleration timing
    - Quarter-mile timing with trap speed
    - G-force calculations
    - Power/torque estimation
    - Track session recording
    - Performance history tracking
    
    All operations are READ-ONLY using standard OBD2 data.
    """
    
    def __init__(self, obd_adapter):
        self.obd_adapter = obd_adapter
        self.logger = None  # Will be set by parent class
        
        # Performance tracking
        self.current_acceleration_event = None
        self.current_session = None
        self.acceleration_history = deque(maxlen=100)
        self.session_history = deque(maxlen=50)
        
        # Data buffers for calculations (last 10 seconds of data)
        self.speed_buffer = deque(maxlen=100)  # 10Hz * 10 seconds
        self.time_buffer = deque(maxlen=100)
        self.rpm_buffer = deque(maxlen=100)
        self.load_buffer = deque(maxlen=100)
        self.boost_buffer = deque(maxlen=100)
        
        # Configuration
        self.sampling_rate = 10  # Hz
        self.auto_detection_enabled = True
        self.g_force_threshold = 0.3  # G's to trigger acceleration detection
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Performance records
        self.personal_bests = {
            "0-60": None,      # Best 0-60 time
            "0-100": None,     # Best 0-100 time
            "quarter_mile": None,  # Best quarter-mile
            "max_g_force": 0.0,
            "max_speed": 0.0,
            "max_power_estimate": 0.0
        }
    
    def update_live_data(self, live_data: Dict[str, Any]) -> None:
        """
        Update performance analytics with live OBD2 data
        
        Args:
            live_data: Current live data from OBD2 adapter
        """
        if not live_data or 'data' not in live_data:
            return
        
        current_time = datetime.now()
        data = live_data['data']
        
        # Extract key performance parameters
        try:
            speed_mph = self._extract_speed(data)
            rpm = self._extract_rpm(data) 
            engine_load = self._extract_load(data)
            boost_pressure = self._extract_boost_pressure(data, live_data.get('bmw_specific', {}))
            
            # Update data buffers
            with self._lock:
                self.speed_buffer.append(speed_mph)
                self.time_buffer.append(current_time)
                self.rpm_buffer.append(rpm)
                self.load_buffer.append(engine_load)
                self.boost_buffer.append(boost_pressure)
            
            # Calculate current G-force
            g_force = self._calculate_g_force()
            
            # Update performance tracking
            self._update_acceleration_tracking(speed_mph, current_time, g_force)
            self._update_session_tracking(current_time, speed_mph, g_force, rpm, engine_load, boost_pressure)
            self._update_personal_bests(speed_mph, g_force)
            
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Performance analytics update error: {e}")
    
    def start_acceleration_timer(self, event_type: str = "0-60") -> str:
        """
        Manually start an acceleration timer
        
        Args:
            event_type: Type of acceleration event ("0-60", "quarter-mile", "custom")
            
        Returns:
            Event ID for tracking
        """
        with self._lock:
            if self.current_acceleration_event and not self.current_acceleration_event.completed:
                # Complete current event first
                self._complete_acceleration_event()
            
            current_speed = self.speed_buffer[-1] if self.speed_buffer else 0.0
            
            self.current_acceleration_event = AccelerationEvent(
                start_time=datetime.now(),
                start_speed=current_speed,
                event_type=event_type
            )
            
            event_id = f"{event_type}_{int(time.time())}"
            return event_id
    
    def stop_acceleration_timer(self) -> Optional[Dict[str, Any]]:
        """
        Manually stop the current acceleration timer
        
        Returns:
            Acceleration event results or None if no active event
        """
        with self._lock:
            if not self.current_acceleration_event or self.current_acceleration_event.completed:
                return None
            
            return self._complete_acceleration_event()
    
    def start_performance_session(self, session_type: str = "track") -> str:
        """
        Start a new performance session for telemetry recording
        
        Args:
            session_type: Type of session ("track", "drag", "street")
            
        Returns:
            Session ID
        """
        with self._lock:
            if self.current_session and not self.current_session.end_time:
                # End current session first
                self.end_performance_session()
            
            session_id = f"{session_type}_{int(time.time())}"
            self.current_session = PerformanceSession(
                session_id=session_id,
                start_time=datetime.now(),
                session_type=session_type
            )
            
            return session_id
    
    def end_performance_session(self) -> Optional[Dict[str, Any]]:
        """
        End the current performance session
        
        Returns:
            Session summary or None if no active session
        """
        with self._lock:
            if not self.current_session or self.current_session.end_time:
                return None
            
            self.current_session.end_time = datetime.now()
            session_dict = asdict(self.current_session)
            
            # Add session to history
            self.session_history.append(self.current_session)
            
            # Calculate session statistics
            session_stats = self._calculate_session_statistics(self.current_session)
            session_dict.update(session_stats)
            
            self.current_session = None
            return session_dict
    
    def get_current_performance_data(self) -> Dict[str, Any]:
        """
        Get current real-time performance data
        
        Returns:
            Current performance metrics
        """
        with self._lock:
            current_time = datetime.now()
            
            # Calculate current metrics
            g_force = self._calculate_g_force()
            power_estimate = self._estimate_power()
            
            current_speed = self.speed_buffer[-1] if self.speed_buffer else 0.0
            current_rpm = self.rpm_buffer[-1] if self.rpm_buffer else 0.0
            current_load = self.load_buffer[-1] if self.load_buffer else 0.0
            current_boost = self.boost_buffer[-1] if self.boost_buffer else 0.0
            
            return {
                'timestamp': current_time.isoformat(),
                'current_metrics': {
                    'speed_mph': round(current_speed, 1),
                    'rpm': int(current_rpm),
                    'engine_load_percent': round(current_load, 1),
                    'boost_pressure_psi': round(current_boost, 2),
                    'g_force_longitudinal': round(g_force, 2),
                    'estimated_power_hp': round(power_estimate, 1)
                },
                'active_events': {
                    'acceleration_timer': self._get_acceleration_status(),
                    'performance_session': self._get_session_status()
                },
                'personal_bests': self.personal_bests.copy()
            }
    
    def get_acceleration_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent acceleration event history
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of acceleration events
        """
        with self._lock:
            history = list(self.acceleration_history)
            history.reverse()  # Most recent first
            return [asdict(event) for event in history[:limit]]
    
    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent session history
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of performance sessions
        """
        with self._lock:
            history = list(self.session_history)
            history.reverse()  # Most recent first
            return [asdict(session) for session in history[:limit]]
    
    def export_telemetry_data(self, session_id: str, format_type: str = "csv") -> Optional[str]:
        """
        Export telemetry data for analysis
        
        Args:
            session_id: Session to export
            format_type: Export format ("csv", "json")
            
        Returns:
            Exported data as string or None if session not found
        """
        # Find session in history
        session = None
        with self._lock:
            for s in self.session_history:
                if s.session_id == session_id:
                    session = s
                    break
        
        if not session or not session.telemetry_points:
            return None
        
        if format_type.lower() == "csv":
            return self._export_csv(session.telemetry_points)
        elif format_type.lower() == "json":
            import json
            return json.dumps(session.telemetry_points, indent=2, default=str)
        else:
            return None
    
    # Private helper methods
    
    def _extract_speed(self, data: Dict[str, Any]) -> float:
        """Extract vehicle speed in mph from OBD2 data"""
        speed_data = data.get('SPEED', {})
        if isinstance(speed_data, dict) and 'value' in speed_data:
            return float(speed_data['value'])
        return 0.0
    
    def _extract_rpm(self, data: Dict[str, Any]) -> float:
        """Extract engine RPM from OBD2 data"""
        rpm_data = data.get('RPM', {})
        if isinstance(rpm_data, dict) and 'value' in rpm_data:
            return float(rpm_data['value'])
        return 0.0
    
    def _extract_load(self, data: Dict[str, Any]) -> float:
        """Extract engine load percentage from OBD2 data"""
        load_data = data.get('ENGINE_LOAD', {})
        if isinstance(load_data, dict) and 'value' in load_data:
            return float(load_data['value'])
        return 0.0
    
    def _extract_boost_pressure(self, data: Dict[str, Any], bmw_data: Dict[str, Any]) -> float:
        """Extract boost pressure from BMW-specific data or calculate from MAP"""
        # Try BMW-specific boost pressure first
        if 'turbo_boost_pressure' in bmw_data:
            return float(bmw_data['turbo_boost_pressure'])
        
        # Fall back to calculating from MAP sensor
        map_data = data.get('INTAKE_PRESSURE', {})
        if isinstance(map_data, dict) and 'value' in map_data:
            # Convert absolute pressure to boost pressure (assuming ~14.7 psi atmospheric)
            map_psi = float(map_data['value'])
            boost_psi = max(0.0, map_psi - 14.7)
            return boost_psi
        
        return 0.0
    
    def _calculate_g_force(self) -> float:
        """Calculate longitudinal G-force from speed changes"""
        if len(self.speed_buffer) < 2 or len(self.time_buffer) < 2:
            return 0.0
        
        # Calculate acceleration from recent speed changes
        recent_speeds = list(self.speed_buffer)[-5:]  # Last 0.5 seconds at 10Hz
        recent_times = list(self.time_buffer)[-5:]
        
        if len(recent_speeds) < 2:
            return 0.0
        
        # Calculate acceleration in mph/s
        time_diff = (recent_times[-1] - recent_times[0]).total_seconds()
        if time_diff <= 0:
            return 0.0
        
        speed_diff = recent_speeds[-1] - recent_speeds[0]
        acceleration_mph_per_sec = speed_diff / time_diff
        
        # Convert to G-force (1 G = 22.369 mph/s)
        g_force = acceleration_mph_per_sec / 22.369
        
        return g_force
    
    def _estimate_power(self) -> float:
        """
        Estimate power output using OBD2 data
        
        This is a simplified estimation based on:
        - Engine load percentage
        - RPM
        - Boost pressure (for turbocharged engines)
        
        Real power would require dyno testing, but this gives a useful estimate.
        """
        if not self.rpm_buffer or not self.load_buffer:
            return 0.0
        
        current_rpm = self.rpm_buffer[-1]
        current_load = self.load_buffer[-1]
        current_boost = self.boost_buffer[-1] if self.boost_buffer else 0.0
        
        # Base power estimation (this is a simplified formula)
        # Actual BMW N63 engine: ~445 HP base, ~520 HP with tune
        base_power = 445  # Base HP for BMW N63 twin-turbo V8
        
        # Load factor (0-100% engine load)
        load_factor = current_load / 100.0
        
        # RPM efficiency curve (peak around 5500 RPM for N63)
        rpm_efficiency = 1.0
        if current_rpm > 0:
            optimal_rpm = 5500
            rpm_efficiency = 1.0 - abs(current_rpm - optimal_rpm) / (optimal_rpm * 2)
            rpm_efficiency = max(0.3, min(1.0, rpm_efficiency))
        
        # Boost factor (additional power from turbocharging)
        boost_factor = 1.0 + (current_boost * 0.02)  # Rough 2% power per PSI of boost
        
        estimated_power = base_power * load_factor * rpm_efficiency * boost_factor
        
        return max(0.0, estimated_power)
    
    def _update_acceleration_tracking(self, speed_mph: float, current_time: datetime, g_force: float) -> None:
        """Update acceleration event tracking"""
        if not self.auto_detection_enabled:
            return
        
        # Auto-detect acceleration events
        if not self.current_acceleration_event:
            # Check if we're starting an acceleration event
            if g_force > self.g_force_threshold and speed_mph < 10:
                self.current_acceleration_event = AccelerationEvent(
                    start_time=current_time,
                    start_speed=speed_mph,
                    event_type="0-60"
                )
        else:
            # Update current event
            event = self.current_acceleration_event
            event.max_speed = max(event.max_speed, speed_mph)
            event.max_g_force = max(event.max_g_force, g_force)
            
            # Check completion conditions
            if event.event_type == "0-60" and speed_mph >= 60:
                event.end_speed = 60.0
                self._complete_acceleration_event()
            elif event.event_type == "quarter-mile":
                # Would need distance calculation for quarter-mile
                pass
    
    def _complete_acceleration_event(self) -> Dict[str, Any]:
        """Complete the current acceleration event"""
        if not self.current_acceleration_event:
            return {}
        
        event = self.current_acceleration_event
        event.end_time = datetime.now()
        event.completed = True
        
        # Calculate final metrics
        duration = (event.end_time - event.start_time).total_seconds()
        
        # Add to history
        self.acceleration_history.append(event)
        
        # Update personal bests
        if event.event_type == "0-60":
            if not self.personal_bests["0-60"] or duration < self.personal_bests["0-60"]:
                self.personal_bests["0-60"] = duration
        
        event_dict = asdict(event)
        event_dict['duration_seconds'] = duration
        
        self.current_acceleration_event = None
        return event_dict
    
    def _update_session_tracking(self, current_time: datetime, speed_mph: float, 
                                g_force: float, rpm: float, engine_load: float, 
                                boost_pressure: float) -> None:
        """Update performance session tracking"""
        if not self.current_session:
            return
        
        session = self.current_session
        
        # Update session maximums
        session.max_speed = max(session.max_speed, speed_mph)
        session.max_g_force = max(session.max_g_force, g_force)
        
        power_estimate = self._estimate_power()
        session.max_power_estimate = max(session.max_power_estimate, power_estimate)
        
        # Track average boost pressure
        if len(session.telemetry_points) > 0:
            total_boost = sum(point.get('boost_pressure', 0) for point in session.telemetry_points)
            session.avg_boost_pressure = (total_boost + boost_pressure) / (len(session.telemetry_points) + 1)
        else:
            session.avg_boost_pressure = boost_pressure
        
        # Add telemetry point (limit frequency to avoid memory issues)
        if (not session.telemetry_points or 
            (current_time - datetime.fromisoformat(session.telemetry_points[-1]['timestamp'])).total_seconds() >= 0.1):
            
            telemetry_point = {
                'timestamp': current_time.isoformat(),
                'speed_mph': speed_mph,
                'rpm': rpm,
                'engine_load': engine_load,
                'boost_pressure': boost_pressure,
                'g_force': g_force,
                'estimated_power': power_estimate
            }
            session.telemetry_points.append(telemetry_point)
    
    def _update_personal_bests(self, speed_mph: float, g_force: float) -> None:
        """Update personal best records"""
        self.personal_bests["max_speed"] = max(self.personal_bests["max_speed"], speed_mph)
        self.personal_bests["max_g_force"] = max(self.personal_bests["max_g_force"], g_force)
        
        power_estimate = self._estimate_power()
        self.personal_bests["max_power_estimate"] = max(self.personal_bests["max_power_estimate"], power_estimate)
    
    def _get_acceleration_status(self) -> Optional[Dict[str, Any]]:
        """Get current acceleration event status"""
        if not self.current_acceleration_event:
            return None
        
        event = self.current_acceleration_event
        duration = (datetime.now() - event.start_time).total_seconds()
        
        return {
            'event_type': event.event_type,
            'start_time': event.start_time.isoformat(),
            'duration_seconds': round(duration, 2),
            'current_speed': event.max_speed,
            'max_g_force': round(event.max_g_force, 2)
        }
    
    def _get_session_status(self) -> Optional[Dict[str, Any]]:
        """Get current session status"""
        if not self.current_session:
            return None
        
        session = self.current_session
        duration = (datetime.now() - session.start_time).total_seconds()
        
        return {
            'session_id': session.session_id,
            'session_type': session.session_type,
            'start_time': session.start_time.isoformat(),
            'duration_seconds': round(duration, 1),
            'telemetry_points': len(session.telemetry_points),
            'max_speed': round(session.max_speed, 1),
            'max_g_force': round(session.max_g_force, 2)
        }
    
    def _calculate_session_statistics(self, session: PerformanceSession) -> Dict[str, Any]:
        """Calculate comprehensive session statistics"""
        if not session.telemetry_points:
            return {}
        
        points = session.telemetry_points
        duration = (session.end_time - session.start_time).total_seconds()
        
        # Calculate various statistics
        speeds = [p['speed_mph'] for p in points]
        g_forces = [p['g_force'] for p in points]
        power_estimates = [p['estimated_power'] for p in points]
        
        stats = {
            'duration_seconds': round(duration, 1),
            'avg_speed': round(sum(speeds) / len(speeds), 1) if speeds else 0,
            'avg_g_force': round(sum(g_forces) / len(g_forces), 2) if g_forces else 0,
            'avg_power_estimate': round(sum(power_estimates) / len(power_estimates), 1) if power_estimates else 0,
            'peak_acceleration_events': self._find_peak_acceleration_events(points),
            'data_quality': self._assess_data_quality(points)
        }
        
        return stats
    
    def _find_peak_acceleration_events(self, telemetry_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find peak acceleration events within session data"""
        events = []
        
        # Simple peak detection - find periods of high G-force
        for i, point in enumerate(telemetry_points):
            if point.get('g_force', 0) > 0.5:  # Significant acceleration
                event_start = i
                max_g = point['g_force']
                
                # Find the peak and end of this acceleration event
                j = i + 1
                while j < len(telemetry_points) and telemetry_points[j].get('g_force', 0) > 0.3:
                    max_g = max(max_g, telemetry_points[j].get('g_force', 0))
                    j += 1
                
                if j > event_start + 5:  # At least 0.5 seconds of acceleration
                    events.append({
                        'start_index': event_start,
                        'end_index': j - 1,
                        'max_g_force': round(max_g, 2),
                        'duration_seconds': round((j - event_start) * 0.1, 1)
                    })
        
        return events[:5]  # Return top 5 events
    
    def _assess_data_quality(self, telemetry_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the quality of telemetry data"""
        if not telemetry_points:
            return {'quality': 'no_data'}
        
        # Check for data consistency and completeness
        missing_fields = 0
        total_fields = len(telemetry_points) * 7  # 7 fields per point
        
        for point in telemetry_points:
            expected_fields = ['timestamp', 'speed_mph', 'rpm', 'engine_load', 
                             'boost_pressure', 'g_force', 'estimated_power']
            for field in expected_fields:
                if field not in point or point[field] is None:
                    missing_fields += 1
        
        completeness = 1.0 - (missing_fields / total_fields)
        
        quality_rating = "excellent" if completeness > 0.95 else \
                        "good" if completeness > 0.85 else \
                        "fair" if completeness > 0.7 else "poor"
        
        return {
            'quality': quality_rating,
            'completeness_percent': round(completeness * 100, 1),
            'total_points': len(telemetry_points),
            'missing_fields': missing_fields
        }
    
    def _export_csv(self, telemetry_points: List[Dict[str, Any]]) -> str:
        """Export telemetry data as CSV format"""
        if not telemetry_points:
            return ""
        
        # CSV header
        headers = list(telemetry_points[0].keys())
        csv_lines = [",".join(headers)]
        
        # CSV data rows
        for point in telemetry_points:
            values = [str(point.get(header, "")) for header in headers]
            csv_lines.append(",".join(values))
        
        return "\n".join(csv_lines)