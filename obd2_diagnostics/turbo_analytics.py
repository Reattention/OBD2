"""
Twin Turbo Advanced Analytics Module

READ-ONLY advanced analytics for BMW twin-turbo engines (e.g., N63).
Provides detailed analysis of turbo performance, balance, efficiency,
and health monitoring using only OBD2 sensor data.
"""

import math
import statistics
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque
import threading


@dataclass
class TurboPerformanceData:
    """Individual turbo performance metrics"""
    timestamp: datetime
    boost_pressure: float  # PSI
    spool_time: Optional[float] = None  # seconds to reach target boost
    efficiency: float = 0.0  # calculated efficiency percentage
    temperature: float = 0.0  # degrees celsius
    wastegate_position: float = 0.0  # percentage open
    compressor_ratio: float = 1.0  # pressure ratio


@dataclass
class TurboBalanceAnalysis:
    """Analysis of balance between two turbos"""
    timestamp: datetime
    turbo1_boost: float
    turbo2_boost: float
    boost_difference: float
    balance_score: float  # 0-100, higher is better balanced
    imbalance_type: str  # "none", "turbo1_high", "turbo2_high", "erratic"


class TurboAnalytics:
    """
    Advanced analytics for BMW twin-turbo systems
    
    Provides comprehensive monitoring and analysis including:
    - Turbo lag analysis and spool time comparison
    - Boost pressure mapping and 3D visualization data
    - Intercooler efficiency monitoring
    - Wastegate position tracking
    - Compressor efficiency visualization
    - Turbo balance analysis and health scoring
    
    All operations are READ-ONLY using standard OBD2 data.
    """
    
    def __init__(self, obd_adapter):
        self.obd_adapter = obd_adapter
        self.logger = None  # Will be set by parent class
        
        # Data storage
        self.turbo1_data = deque(maxlen=1000)  # 100 seconds at 10Hz
        self.turbo2_data = deque(maxlen=1000)
        self.balance_history = deque(maxlen=500)
        
        # Analysis buffers
        self.boost_map_data = {}  # RPM/Load -> Boost pressure mapping
        self.spool_events = deque(maxlen=50)  # Recent spool time measurements
        
        # Configuration for BMW N63 twin-turbo
        self.engine_config = {
            "max_boost_psi": 18.0,      # Maximum expected boost
            "target_boost_psi": 15.5,   # Typical target boost at WOT
            "spool_threshold_psi": 5.0, # Minimum boost to consider "spooled"
            "balance_tolerance_psi": 2.0, # Acceptable difference between turbos
            "intercooler_target_temp": 40.0,  # Target intercooler outlet temp (C)
            "max_egt_celsius": 850.0    # Maximum safe EGT
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Health tracking
        self.turbo_health_scores = {
            "turbo1": 100.0,
            "turbo2": 100.0,
            "overall": 100.0
        }
        
        # Performance tracking
        self.performance_metrics = {
            "avg_spool_time_turbo1": 0.0,
            "avg_spool_time_turbo2": 0.0,
            "best_balance_score": 0.0,
            "avg_intercooler_efficiency": 0.0,
            "total_boost_events": 0
        }
    
    def update_turbo_data(self, live_data: Dict[str, Any]) -> None:
        """
        Update turbo analytics with live OBD2 data
        
        Args:
            live_data: Current live data from OBD2 adapter
        """
        if not live_data or 'data' not in live_data:
            return
        
        current_time = datetime.now()
        data = live_data['data']
        bmw_data = live_data.get('bmw_specific', {})
        
        try:
            # Extract turbo-related data
            boost_pressure = self._extract_boost_pressure(data, bmw_data)
            intake_temp = self._extract_intake_temperature(data)
            ambient_temp = self._extract_ambient_temperature(data)
            rpm = self._extract_rpm(data)
            engine_load = self._extract_load(data)
            throttle_position = self._extract_throttle_position(data)
            
            # For twin-turbo systems, we need to estimate individual turbo data
            # In reality, this would require bank-specific sensors
            turbo1_boost, turbo2_boost = self._estimate_individual_turbo_boost(
                boost_pressure, rpm, engine_load, bmw_data
            )
            
            # Calculate derived metrics
            intercooler_efficiency = self._calculate_intercooler_efficiency(
                intake_temp, ambient_temp
            )
            
            compressor_ratio1 = self._calculate_compressor_ratio(turbo1_boost)
            compressor_ratio2 = self._calculate_compressor_ratio(turbo2_boost)
            
            # Create turbo performance data
            turbo1_perf = TurboPerformanceData(
                timestamp=current_time,
                boost_pressure=turbo1_boost,
                efficiency=intercooler_efficiency,
                temperature=intake_temp,
                compressor_ratio=compressor_ratio1
            )
            
            turbo2_perf = TurboPerformanceData(
                timestamp=current_time,
                boost_pressure=turbo2_boost,
                efficiency=intercooler_efficiency,
                temperature=intake_temp,
                compressor_ratio=compressor_ratio2
            )
            
            # Update data storage
            with self._lock:
                self.turbo1_data.append(turbo1_perf)
                self.turbo2_data.append(turbo2_perf)
                
                # Update boost mapping
                self._update_boost_map(rpm, engine_load, boost_pressure)
                
                # Analyze turbo balance
                self._analyze_turbo_balance(turbo1_boost, turbo2_boost, current_time)
                
                # Detect and analyze spool events
                self._analyze_spool_events(throttle_position, turbo1_boost, turbo2_boost, current_time)
                
                # Update health scores
                self._update_health_scores()
        
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Turbo analytics update error: {e}")
    
    def get_turbo_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive turbo performance summary
        
        Returns:
            Detailed turbo performance data
        """
        with self._lock:
            current_time = datetime.now()
            
            # Get latest data
            latest_turbo1 = self.turbo1_data[-1] if self.turbo1_data else None
            latest_turbo2 = self.turbo2_data[-1] if self.turbo2_data else None
            latest_balance = self.balance_history[-1] if self.balance_history else None
            
            summary = {
                'timestamp': current_time.isoformat(),
                'current_performance': {
                    'turbo1': asdict(latest_turbo1) if latest_turbo1 else None,
                    'turbo2': asdict(latest_turbo2) if latest_turbo2 else None,
                    'balance': asdict(latest_balance) if latest_balance else None
                },
                'health_scores': self.turbo_health_scores.copy(),
                'performance_metrics': self.performance_metrics.copy(),
                'recent_analysis': {
                    'avg_spool_time': self._calculate_average_spool_time(),
                    'balance_trend': self._analyze_balance_trend(),
                    'efficiency_trend': self._analyze_efficiency_trend(),
                    'temperature_analysis': self._analyze_temperature_trends()
                }
            }
            
            return summary
    
    def get_boost_pressure_map(self, rpm_range: Tuple[int, int] = (1000, 7000), 
                              load_range: Tuple[int, int] = (0, 100)) -> Dict[str, Any]:
        """
        Get 3D boost pressure mapping data for visualization
        
        Args:
            rpm_range: RPM range for mapping (min, max)
            load_range: Engine load range for mapping (min, max)
            
        Returns:
            3D mapping data for boost pressure visualization
        """
        with self._lock:
            # Create RPM and load grids
            rpm_step = 250
            load_step = 10
            
            rpm_points = list(range(rpm_range[0], rpm_range[1] + rpm_step, rpm_step))
            load_points = list(range(load_range[0], load_range[1] + load_step, load_step))
            
            # Generate boost map data
            boost_map = []
            for rpm in rpm_points:
                rpm_data = []
                for load in load_points:
                    # Get boost pressure for this RPM/load combination
                    boost = self._get_boost_for_rpm_load(rpm, load)
                    rpm_data.append({
                        'rpm': rpm,
                        'load': load,
                        'boost_psi': boost,
                        'efficiency': self._estimate_efficiency_for_point(rpm, load, boost)
                    })
                boost_map.append(rpm_data)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'rpm_range': rpm_range,
                'load_range': load_range,
                'boost_map': boost_map,
                'map_metadata': {
                    'total_points': len(rpm_points) * len(load_points),
                    'rpm_resolution': rpm_step,
                    'load_resolution': load_step,
                    'data_points_collected': len(self.boost_map_data)
                }
            }
    
    def get_turbo_lag_analysis(self) -> Dict[str, Any]:
        """
        Get detailed turbo lag analysis and spool time comparison
        
        Returns:
            Comprehensive turbo lag analysis
        """
        with self._lock:
            if len(self.spool_events) < 5:
                return {
                    'error': 'Insufficient spool event data',
                    'events_recorded': len(self.spool_events),
                    'minimum_required': 5
                }
            
            # Analyze recent spool events
            recent_events = list(self.spool_events)[-20:]  # Last 20 events
            
            turbo1_times = []
            turbo2_times = []
            
            for event in recent_events:
                if 'turbo1_spool_time' in event and event['turbo1_spool_time'] > 0:
                    turbo1_times.append(event['turbo1_spool_time'])
                if 'turbo2_spool_time' in event and event['turbo2_spool_time'] > 0:
                    turbo2_times.append(event['turbo2_spool_time'])
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'spool_time_analysis': {
                    'turbo1': self._analyze_spool_times(turbo1_times, "Turbo 1"),
                    'turbo2': self._analyze_spool_times(turbo2_times, "Turbo 2")
                },
                'comparison': {},
                'recent_events': recent_events,
                'recommendations': []
            }
            
            # Compare turbo performance
            if turbo1_times and turbo2_times:
                avg_t1 = statistics.mean(turbo1_times)
                avg_t2 = statistics.mean(turbo2_times)
                
                analysis['comparison'] = {
                    'avg_difference_seconds': round(abs(avg_t1 - avg_t2), 3),
                    'faster_turbo': "turbo1" if avg_t1 < avg_t2 else "turbo2",
                    'performance_balance': "good" if abs(avg_t1 - avg_t2) < 0.2 else "needs_attention"
                }
                
                # Generate recommendations
                if abs(avg_t1 - avg_t2) > 0.5:
                    slower_turbo = "Turbo 1" if avg_t1 > avg_t2 else "Turbo 2"
                    analysis['recommendations'].append(
                        f"{slower_turbo} shows slower spool times. Check for boost leaks or wastegate issues."
                    )
            
            return analysis
    
    def get_intercooler_efficiency_data(self) -> Dict[str, Any]:
        """
        Get intercooler efficiency monitoring data
        
        Returns:
            Intercooler efficiency analysis
        """
        with self._lock:
            if not self.turbo1_data:
                return {'error': 'No intercooler data available'}
            
            # Analyze recent efficiency data
            recent_data = list(self.turbo1_data)[-100:]  # Last 10 seconds
            efficiencies = [data.efficiency for data in recent_data if data.efficiency > 0]
            temperatures = [data.temperature for data in recent_data if data.temperature > 0]
            
            if not efficiencies or not temperatures:
                return {'error': 'Insufficient efficiency data'}
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'current_efficiency': {
                    'efficiency_percent': round(efficiencies[-1], 1),
                    'intake_temp_celsius': round(temperatures[-1], 1),
                    'status': self._assess_intercooler_status(efficiencies[-1], temperatures[-1])
                },
                'performance_trends': {
                    'avg_efficiency': round(statistics.mean(efficiencies), 1),
                    'min_efficiency': round(min(efficiencies), 1),
                    'max_efficiency': round(max(efficiencies), 1),
                    'efficiency_stability': self._calculate_efficiency_stability(efficiencies)
                },
                'temperature_analysis': {
                    'avg_temp': round(statistics.mean(temperatures), 1),
                    'temp_range': round(max(temperatures) - min(temperatures), 1),
                    'heat_soak_indicator': self._assess_heat_soak(temperatures)
                },
                'recommendations': self._generate_intercooler_recommendations(efficiencies, temperatures)
            }
            
            return analysis
    
    def get_wastegate_analysis(self) -> Dict[str, Any]:
        """
        Get wastegate position tracking and analysis
        
        Returns:
            Wastegate performance analysis
        """
        # Note: Actual wastegate position data would require specific BMW PIDs
        # This provides a framework for when such data becomes available
        
        with self._lock:
            current_time = datetime.now()
            
            # Estimate wastegate behavior from boost pressure patterns
            if not self.turbo1_data:
                return {'error': 'Insufficient data for wastegate analysis'}
                
            boost_data = [data.boost_pressure for data in list(self.turbo1_data)[-50:]]
            
            if len(boost_data) < 10:
                return {'error': 'Insufficient data for wastegate analysis'}
            
            analysis = {
                'timestamp': current_time.isoformat(),
                'estimated_wastegate_behavior': {
                    'boost_stability': self._analyze_boost_stability(boost_data),
                    'overboost_events': self._detect_overboost_events(boost_data),
                    'underboost_events': self._detect_underboost_events(boost_data),
                    'wastegate_health_estimate': self._estimate_wastegate_health(boost_data)
                },
                'note': 'Analysis based on boost pressure patterns. Direct wastegate position requires specific BMW PIDs.'
            }
            
            return analysis
    
    def get_compressor_efficiency_map(self) -> Dict[str, Any]:
        """
        Get compressor efficiency visualization data
        
        Returns:
            Data for compressor efficiency map visualization
        """
        with self._lock:
            if not self.turbo1_data or not self.turbo2_data:
                return {'error': 'Insufficient compressor data'}
            
            # Create compressor efficiency map data
            efficiency_points = []
            
            for t1_data, t2_data in zip(list(self.turbo1_data)[-100:], list(self.turbo2_data)[-100:]):
                # Calculate mass flow estimate (simplified)
                mass_flow = self._estimate_mass_flow(t1_data.boost_pressure, t1_data.temperature)
                
                efficiency_points.append({
                    'timestamp': t1_data.timestamp.isoformat(),
                    'turbo1': {
                        'pressure_ratio': t1_data.compressor_ratio,
                        'mass_flow_estimate': mass_flow,
                        'efficiency_estimate': t1_data.efficiency,
                        'operating_point_health': self._assess_operating_point(t1_data.compressor_ratio, mass_flow)
                    },
                    'turbo2': {
                        'pressure_ratio': t2_data.compressor_ratio,
                        'mass_flow_estimate': mass_flow,
                        'efficiency_estimate': t2_data.efficiency,
                        'operating_point_health': self._assess_operating_point(t2_data.compressor_ratio, mass_flow)
                    }
                })
            
            return {
                'timestamp': datetime.now().isoformat(),
                'efficiency_map_data': efficiency_points,
                'compressor_specifications': {
                    'optimal_pressure_ratio_range': [1.5, 2.8],
                    'optimal_efficiency_range': [65, 80],
                    'surge_line_warning': 'Monitor for pressure ratios > 3.0 at low flow',
                    'choke_line_warning': 'Monitor for mass flow > design limits'
                }
            }
    
    # Private helper methods
    
    def _extract_boost_pressure(self, data: Dict[str, Any], bmw_data: Dict[str, Any]) -> float:
        """Extract boost pressure from OBD2 data"""
        # Try BMW-specific boost pressure first
        if 'turbo_boost_pressure' in bmw_data:
            return float(bmw_data['turbo_boost_pressure'])
        
        # Fall back to MAP sensor calculation
        map_data = data.get('INTAKE_PRESSURE', {})
        if isinstance(map_data, dict) and 'value' in map_data:
            map_psi = float(map_data['value'])
            boost_psi = max(0.0, map_psi - 14.7)  # Atmospheric pressure subtraction
            return boost_psi
        
        return 0.0
    
    def _extract_intake_temperature(self, data: Dict[str, Any]) -> float:
        """Extract intake air temperature"""
        temp_data = data.get('INTAKE_TEMP', {})
        if isinstance(temp_data, dict) and 'value' in temp_data:
            return float(temp_data['value'])
        return 25.0  # Default ambient temperature
    
    def _extract_ambient_temperature(self, data: Dict[str, Any]) -> float:
        """Extract ambient air temperature"""
        temp_data = data.get('AMBIANT_AIR_TEMP', {})
        if isinstance(temp_data, dict) and 'value' in temp_data:
            return float(temp_data['value'])
        return 25.0  # Default ambient temperature
    
    def _extract_rpm(self, data: Dict[str, Any]) -> float:
        """Extract engine RPM"""
        rpm_data = data.get('RPM', {})
        if isinstance(rpm_data, dict) and 'value' in rpm_data:
            return float(rpm_data['value'])
        return 0.0
    
    def _extract_load(self, data: Dict[str, Any]) -> float:
        """Extract engine load percentage"""
        load_data = data.get('ENGINE_LOAD', {})
        if isinstance(load_data, dict) and 'value' in load_data:
            return float(load_data['value'])
        return 0.0
    
    def _extract_throttle_position(self, data: Dict[str, Any]) -> float:
        """Extract throttle position percentage"""
        throttle_data = data.get('THROTTLE_POS', {})
        if isinstance(throttle_data, dict) and 'value' in throttle_data:
            return float(throttle_data['value'])
        return 0.0
    
    def _estimate_individual_turbo_boost(self, total_boost: float, rpm: float, 
                                       load: float, bmw_data: Dict[str, Any]) -> Tuple[float, float]:
        """
        Estimate individual turbo boost pressures
        
        In a real implementation, this would use bank-specific sensors.
        For now, we simulate slight differences based on engine characteristics.
        """
        # For twin-turbo systems, turbos typically have slight variations
        # Simulate based on RPM and load characteristics
        
        base_variation = 0.1  # Base 0.1 PSI difference
        rpm_factor = (rpm - 3000) / 10000  # RPM-based variation
        load_factor = load / 1000  # Load-based variation
        
        variation = base_variation + rpm_factor + load_factor
        variation = max(-0.5, min(0.5, variation))  # Limit to ±0.5 PSI
        
        turbo1_boost = total_boost + variation
        turbo2_boost = total_boost - variation
        
        return max(0.0, turbo1_boost), max(0.0, turbo2_boost)
    
    def _calculate_intercooler_efficiency(self, intake_temp: float, ambient_temp: float) -> float:
        """Calculate intercooler efficiency percentage"""
        if ambient_temp <= 0:
            return 0.0
        
        # Simplified intercooler efficiency calculation
        # Perfect efficiency would cool to ambient temp
        temp_drop = max(0, intake_temp - ambient_temp)
        
        # Assume compressed air would be ~60°C hotter without intercooler
        theoretical_max_temp = ambient_temp + 60
        max_possible_drop = theoretical_max_temp - ambient_temp
        
        if max_possible_drop <= 0:
            return 100.0
        
        efficiency = ((max_possible_drop - temp_drop) / max_possible_drop) * 100
        return max(0.0, min(100.0, efficiency))
    
    def _calculate_compressor_ratio(self, boost_pressure: float) -> float:
        """Calculate compressor pressure ratio"""
        atmospheric_pressure = 14.7  # PSI
        absolute_pressure = atmospheric_pressure + boost_pressure
        return absolute_pressure / atmospheric_pressure
    
    def _update_boost_map(self, rpm: float, load: float, boost: float) -> None:
        """Update boost pressure mapping data"""
        # Round to nearest mapping points
        rpm_key = round(rpm / 250) * 250
        load_key = round(load / 10) * 10
        
        map_key = (rpm_key, load_key)
        
        if map_key not in self.boost_map_data:
            self.boost_map_data[map_key] = []
        
        self.boost_map_data[map_key].append({
            'boost': boost,
            'timestamp': datetime.now()
        })
        
        # Keep only recent data (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.boost_map_data[map_key] = [
            data for data in self.boost_map_data[map_key] 
            if data['timestamp'] > cutoff_time
        ]
    
    def _analyze_turbo_balance(self, turbo1_boost: float, turbo2_boost: float, timestamp: datetime) -> None:
        """Analyze balance between turbos"""
        boost_diff = abs(turbo1_boost - turbo2_boost)
        
        # Calculate balance score (0-100, higher is better)
        max_acceptable_diff = self.engine_config["balance_tolerance_psi"]
        balance_score = max(0, 100 - (boost_diff / max_acceptable_diff) * 100)
        
        # Determine imbalance type
        imbalance_type = "none"
        if boost_diff > max_acceptable_diff:
            if turbo1_boost > turbo2_boost:
                imbalance_type = "turbo1_high"
            else:
                imbalance_type = "turbo2_high"
        
        balance_analysis = TurboBalanceAnalysis(
            timestamp=timestamp,
            turbo1_boost=turbo1_boost,
            turbo2_boost=turbo2_boost,
            boost_difference=boost_diff,
            balance_score=balance_score,
            imbalance_type=imbalance_type
        )
        
        self.balance_history.append(balance_analysis)
    
    def _analyze_spool_events(self, throttle_position: float, turbo1_boost: float, 
                            turbo2_boost: float, timestamp: datetime) -> None:
        """Detect and analyze turbo spool events"""
        # Simple spool detection: throttle opens and boost rises
        if (throttle_position > 80 and  # Wide open throttle
            (turbo1_boost > self.engine_config["spool_threshold_psi"] or 
             turbo2_boost > self.engine_config["spool_threshold_psi"])):
            
            # Check if this is a new spool event
            if (not self.spool_events or 
                (timestamp - self.spool_events[-1]['timestamp']).total_seconds() > 5):
                
                spool_event = {
                    'timestamp': timestamp,
                    'throttle_position': throttle_position,
                    'turbo1_boost': turbo1_boost,
                    'turbo2_boost': turbo2_boost,
                    'turbo1_spool_time': self._estimate_spool_time(turbo1_boost),
                    'turbo2_spool_time': self._estimate_spool_time(turbo2_boost)
                }
                
                self.spool_events.append(spool_event)
    
    def _estimate_spool_time(self, boost_pressure: float) -> float:
        """Estimate spool time based on boost pressure"""
        # Simplified spool time estimation
        # Real implementation would track boost rise rate
        
        target_boost = self.engine_config["target_boost_psi"]
        if boost_pressure < self.engine_config["spool_threshold_psi"]:
            return 0.0
        
        # Estimate based on boost achieved vs target
        spool_ratio = boost_pressure / target_boost
        estimated_time = 2.0 - (spool_ratio * 1.5)  # 0.5-2.0 seconds typical range
        
        return max(0.5, min(2.5, estimated_time))
    
    def _update_health_scores(self) -> None:
        """Update turbo health scores based on recent performance"""
        if len(self.balance_history) < 10:
            return
        
        recent_balance = list(self.balance_history)[-10:]
        avg_balance_score = statistics.mean([b.balance_score for b in recent_balance])
        
        # Update health scores based on balance performance
        self.turbo_health_scores["overall"] = (avg_balance_score + 100) / 2
        
        # Individual turbo scores based on consistency
        turbo1_consistency = self._calculate_turbo_consistency("turbo1")
        turbo2_consistency = self._calculate_turbo_consistency("turbo2")
        
        self.turbo_health_scores["turbo1"] = turbo1_consistency
        self.turbo_health_scores["turbo2"] = turbo2_consistency
    
    def _calculate_turbo_consistency(self, turbo_name: str) -> float:
        """Calculate consistency score for individual turbo"""
        data_source = self.turbo1_data if turbo_name == "turbo1" else self.turbo2_data
        
        if len(data_source) < 20:
            return 100.0
        
        recent_boost = [data.boost_pressure for data in list(data_source)[-20:]]
        
        if not recent_boost or max(recent_boost) < 2.0:
            return 100.0  # No boost activity to evaluate
        
        # Calculate coefficient of variation
        boost_mean = statistics.mean(recent_boost)
        boost_stdev = statistics.stdev(recent_boost) if len(recent_boost) > 1 else 0
        
        if boost_mean == 0:
            return 100.0
        
        cv = boost_stdev / boost_mean
        consistency_score = max(0, 100 - (cv * 200))  # Convert to 0-100 scale
        
        return consistency_score
    
    def _get_boost_for_rpm_load(self, rpm: int, load: int) -> float:
        """Get boost pressure for specific RPM/load combination"""
        map_key = (rpm, load)
        
        if map_key in self.boost_map_data and self.boost_map_data[map_key]:
            # Return average of recorded values
            boost_values = [data['boost'] for data in self.boost_map_data[map_key]]
            return statistics.mean(boost_values)
        
        # Estimate based on nearby points or engine characteristics
        return self._estimate_boost_for_rpm_load(rpm, load)
    
    def _estimate_boost_for_rpm_load(self, rpm: int, load: int) -> float:
        """Estimate boost pressure for RPM/load combination"""
        # Simplified boost estimation for BMW N63
        # Real implementation would use engine maps
        
        if load < 20:
            return 0.0  # No boost at low load
        
        # Peak boost around 3000-5500 RPM
        rpm_factor = 1.0
        if rpm < 2000:
            rpm_factor = 0.3
        elif rpm < 3000:
            rpm_factor = 0.7 + (rpm - 2000) / 3333
        elif rpm <= 5500:
            rpm_factor = 1.0
        else:
            rpm_factor = 1.0 - (rpm - 5500) / 5000
        
        load_factor = load / 100.0
        max_boost = self.engine_config["target_boost_psi"]
        
        estimated_boost = max_boost * rpm_factor * load_factor
        return max(0.0, estimated_boost)
    
    def _estimate_efficiency_for_point(self, rpm: int, load: int, boost: float) -> float:
        """Estimate compressor efficiency for operating point"""
        pressure_ratio = self._calculate_compressor_ratio(boost)
        
        # Simplified efficiency map
        # Peak efficiency typically around PR 2.0-2.5
        if pressure_ratio < 1.2:
            return 60.0  # Low efficiency at low pressure ratios
        elif pressure_ratio < 2.0:
            return 60.0 + (pressure_ratio - 1.2) * 25  # Rising efficiency
        elif pressure_ratio <= 2.5:
            return 80.0  # Peak efficiency
        else:
            return 80.0 - (pressure_ratio - 2.5) * 20  # Declining efficiency
    
    def _calculate_average_spool_time(self) -> Dict[str, float]:
        """Calculate average spool times for both turbos"""
        if not self.spool_events:
            return {'turbo1': 0.0, 'turbo2': 0.0}
        
        recent_events = list(self.spool_events)[-10:]
        
        turbo1_times = [e['turbo1_spool_time'] for e in recent_events if e['turbo1_spool_time'] > 0]
        turbo2_times = [e['turbo2_spool_time'] for e in recent_events if e['turbo2_spool_time'] > 0]
        
        return {
            'turbo1': statistics.mean(turbo1_times) if turbo1_times else 0.0,
            'turbo2': statistics.mean(turbo2_times) if turbo2_times else 0.0
        }
    
    def _analyze_balance_trend(self) -> Dict[str, Any]:
        """Analyze balance trends over time"""
        if len(self.balance_history) < 5:
            return {'trend': 'insufficient_data'}
        
        recent_scores = [b.balance_score for b in list(self.balance_history)[-20:]]
        
        # Simple trend analysis
        first_half_avg = statistics.mean(recent_scores[:len(recent_scores)//2])
        second_half_avg = statistics.mean(recent_scores[len(recent_scores)//2:])
        
        trend_direction = "improving" if second_half_avg > first_half_avg else \
                         "declining" if second_half_avg < first_half_avg else "stable"
        
        return {
            'trend': trend_direction,
            'recent_avg_score': round(statistics.mean(recent_scores), 1),
            'score_change': round(second_half_avg - first_half_avg, 1)
        }
    
    def _analyze_efficiency_trend(self) -> Dict[str, Any]:
        """Analyze efficiency trends"""
        if not self.turbo1_data:
            return {'trend': 'no_data'}
        
        recent_efficiencies = [data.efficiency for data in list(self.turbo1_data)[-50:]]
        
        if len(recent_efficiencies) < 10:
            return {'trend': 'insufficient_data'}
        
        avg_efficiency = statistics.mean(recent_efficiencies)
        
        return {
            'avg_efficiency': round(avg_efficiency, 1),
            'trend': 'stable',  # Simplified trend analysis
            'status': 'good' if avg_efficiency > 70 else 'fair' if avg_efficiency > 50 else 'poor'
        }
    
    def _analyze_temperature_trends(self) -> Dict[str, Any]:
        """Analyze temperature trends"""
        if not self.turbo1_data:
            return {'trend': 'no_data'}
        
        recent_temps = [data.temperature for data in list(self.turbo1_data)[-30:]]
        
        if len(recent_temps) < 5:
            return {'trend': 'insufficient_data'}
        
        avg_temp = statistics.mean(recent_temps)
        max_temp = max(recent_temps)
        
        return {
            'avg_temperature': round(avg_temp, 1),
            'max_temperature': round(max_temp, 1),
            'status': self._assess_temperature_status(avg_temp, max_temp)
        }
    
    def _analyze_spool_times(self, spool_times: List[float], turbo_name: str) -> Dict[str, Any]:
        """Analyze spool time data for a specific turbo"""
        if not spool_times:
            return {'status': 'no_data', 'turbo': turbo_name}
        
        avg_time = statistics.mean(spool_times)
        min_time = min(spool_times)
        max_time = max(spool_times)
        consistency = statistics.stdev(spool_times) if len(spool_times) > 1 else 0
        
        # Assess performance
        performance_rating = "excellent" if avg_time < 1.2 else \
                           "good" if avg_time < 1.8 else \
                           "fair" if avg_time < 2.5 else "poor"
        
        return {
            'turbo': turbo_name,
            'avg_spool_time': round(avg_time, 2),
            'min_spool_time': round(min_time, 2),
            'max_spool_time': round(max_time, 2),
            'consistency_stdev': round(consistency, 3),
            'performance_rating': performance_rating,
            'sample_size': len(spool_times)
        }
    
    def _assess_intercooler_status(self, efficiency: float, temperature: float) -> str:
        """Assess intercooler performance status"""
        if efficiency > 80 and temperature < 50:
            return "excellent"
        elif efficiency > 70 and temperature < 60:
            return "good"
        elif efficiency > 60 and temperature < 75:
            return "fair"
        else:
            return "poor"
    
    def _calculate_efficiency_stability(self, efficiencies: List[float]) -> str:
        """Calculate efficiency stability rating"""
        if len(efficiencies) < 5:
            return "insufficient_data"
        
        stdev = statistics.stdev(efficiencies)
        
        if stdev < 5:
            return "very_stable"
        elif stdev < 10:
            return "stable"
        elif stdev < 15:
            return "moderate"
        else:
            return "unstable"
    
    def _assess_heat_soak(self, temperatures: List[float]) -> str:
        """Assess heat soak indicator"""
        if len(temperatures) < 10:
            return "insufficient_data"
        
        temp_rise = max(temperatures) - min(temperatures)
        
        if temp_rise < 10:
            return "minimal"
        elif temp_rise < 20:
            return "moderate"
        else:
            return "significant"
    
    def _generate_intercooler_recommendations(self, efficiencies: List[float], 
                                            temperatures: List[float]) -> List[str]:
        """Generate intercooler maintenance recommendations"""
        recommendations = []
        
        if efficiencies and statistics.mean(efficiencies) < 60:
            recommendations.append("Intercooler efficiency is low. Check for clogs or damage.")
        
        if temperatures and max(temperatures) > 80:
            recommendations.append("High intake temperatures detected. Consider intercooler upgrade.")
        
        if (temperatures and len(temperatures) > 10 and 
            max(temperatures) - min(temperatures) > 25):
            recommendations.append("Significant temperature variation indicates heat soak issues.")
        
        return recommendations
    
    def _analyze_boost_stability(self, boost_data: List[float]) -> Dict[str, Any]:
        """Analyze boost pressure stability"""
        if len(boost_data) < 5:
            return {'status': 'insufficient_data'}
        
        stdev = statistics.stdev(boost_data) if len(boost_data) > 1 else 0
        mean_boost = statistics.mean(boost_data)
        
        stability_rating = "excellent" if stdev < 0.5 else \
                          "good" if stdev < 1.0 else \
                          "fair" if stdev < 2.0 else "poor"
        
        return {
            'stability_rating': stability_rating,
            'boost_variation_psi': round(stdev, 2),
            'mean_boost_psi': round(mean_boost, 2)
        }
    
    def _detect_overboost_events(self, boost_data: List[float]) -> List[Dict[str, Any]]:
        """Detect overboost events"""
        events = []
        max_boost = self.engine_config["max_boost_psi"]
        
        for i, boost in enumerate(boost_data):
            if boost > max_boost:
                events.append({
                    'index': i,
                    'boost_psi': round(boost, 2),
                    'overboost_amount': round(boost - max_boost, 2)
                })
        
        return events
    
    def _detect_underboost_events(self, boost_data: List[float]) -> List[Dict[str, Any]]:
        """Detect underboost events"""
        events = []
        target_boost = self.engine_config["target_boost_psi"]
        underboost_threshold = target_boost * 0.8  # 80% of target
        
        for i, boost in enumerate(boost_data):
            if boost < underboost_threshold and boost > 2.0:  # Only count when trying to boost
                events.append({
                    'index': i,
                    'boost_psi': round(boost, 2),
                    'underboost_amount': round(target_boost - boost, 2)
                })
        
        return events
    
    def _estimate_wastegate_health(self, boost_data: List[float]) -> str:
        """Estimate wastegate health from boost patterns"""
        overboost_events = self._detect_overboost_events(boost_data)
        underboost_events = self._detect_underboost_events(boost_data)
        stability = self._analyze_boost_stability(boost_data)
        
        if len(overboost_events) > 3:
            return "poor_wastegate_may_be_stuck_closed"
        elif len(underboost_events) > 5:
            return "poor_wastegate_may_be_stuck_open_or_boost_leak"
        elif stability['stability_rating'] in ['poor', 'fair']:
            return "fair_wastegate_response_inconsistent"
        else:
            return "good"
    
    def _estimate_mass_flow(self, boost_pressure: float, temperature: float) -> float:
        """Estimate mass flow rate (simplified calculation)"""
        # Simplified mass flow estimation
        # Real calculation would need more detailed engine data
        
        pressure_ratio = self._calculate_compressor_ratio(boost_pressure)
        temp_kelvin = temperature + 273.15
        
        # Simplified flow estimation based on pressure ratio and temperature
        estimated_flow = (pressure_ratio - 1) * 100 / (temp_kelvin / 300)
        
        return max(0.0, estimated_flow)
    
    def _assess_operating_point(self, pressure_ratio: float, mass_flow: float) -> str:
        """Assess compressor operating point health"""
        # Simplified assessment
        if pressure_ratio > 3.0:
            return "approaching_surge_line"
        elif pressure_ratio < 1.3:
            return "low_efficiency_region"
        elif 1.5 <= pressure_ratio <= 2.5:
            return "optimal_efficiency_region"
        else:
            return "moderate_efficiency_region"
    
    def _assess_temperature_status(self, avg_temp: float, max_temp: float) -> str:
        """Assess temperature status"""
        if max_temp > 90:
            return "critical_high_temperature"
        elif max_temp > 75:
            return "high_temperature"
        elif avg_temp > 60:
            return "elevated_temperature"
        else:
            return "normal_temperature"