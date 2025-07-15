"""
Predictive Maintenance AI Module

READ-ONLY predictive maintenance analysis for BMW vehicles.
Uses machine learning patterns and statistical analysis on OBD2 data
to predict maintenance needs and component health without any ECU modifications.
"""

import statistics
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from enum import Enum
import threading


class MaintenanceUrgency(Enum):
    """Maintenance urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComponentHealth(Enum):
    """Component health status"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class MaintenanceAlert:
    """Maintenance alert data structure"""
    component: str
    alert_type: str
    urgency: MaintenanceUrgency
    confidence: float  # 0-1 confidence level
    description: str
    recommendation: str
    estimated_days_remaining: Optional[int] = None
    related_dtcs: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.related_dtcs is None:
            self.related_dtcs = []


@dataclass
class ComponentHealthScore:
    """Health score for a specific component"""
    component: str
    health_score: float  # 0-100
    health_status: ComponentHealth
    wear_rate: float  # degradation rate per 1000 miles
    estimated_lifespan_miles: Optional[int] = None
    confidence: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class PredictiveMaintenance:
    """
    BMW-specific predictive maintenance AI engine
    
    Analyzes patterns in OBD2 data to predict maintenance needs including:
    - Oil change recommendations based on driving conditions
    - Turbo health scoring and degradation prediction
    - DTC pattern analysis and failure prediction
    - Component lifespan estimation
    - BMW-specific maintenance alerts
    - Wear prediction based on operating conditions
    
    All analysis is READ-ONLY using historical OBD2 data patterns.
    """
    
    def __init__(self, obd_adapter):
        self.obd_adapter = obd_adapter
        self.logger = None  # Will be set by parent class
        
        # Historical data storage
        self.historical_data = deque(maxlen=10000)  # Store last 10k data points
        self.maintenance_history = deque(maxlen=100)  # Maintenance events
        self.dtc_patterns = defaultdict(list)  # DTC occurrence patterns
        
        # Component health tracking
        self.component_health = {}
        self.wear_patterns = defaultdict(list)
        
        # BMW-specific maintenance intervals (miles)
        self.bmw_maintenance_intervals = {
            "oil_change": 10000,      # BMW Condition Based Service
            "spark_plugs": 60000,     # N63 engine
            "air_filter": 30000,
            "fuel_filter": 60000,
            "brake_fluid": 24000,     # 2 years
            "coolant": 100000,        # Lifetime fill
            "transmission_fluid": 100000,
            "turbo_service": 80000,   # Turbocharger maintenance
            "carbon_cleaning": 40000, # Direct injection engines
            "walnut_blasting": 40000  # Intake valve cleaning
        }
        
        # Current vehicle state
        self.current_mileage = 0
        self.last_oil_change_mileage = 0
        self.driving_conditions = "normal"  # normal, severe, highway, city
        
        # Alert thresholds
        self.alert_thresholds = {
            "oil_life_percent": 15,        # Alert when oil life < 15%
            "coolant_temp_celsius": 110,   # High coolant temperature
            "turbo_health_score": 70,      # Turbo health below 70%
            "misfire_rate_percent": 2,     # Misfire rate above 2%
            "fuel_trim_percent": 15        # Fuel trim beyond ±15%
        }
        
        # Machine learning patterns
        self.pattern_database = {
            "oil_degradation_patterns": [],
            "turbo_failure_precursors": [],
            "injection_system_patterns": [],
            "cooling_system_patterns": [],
            "dtc_sequence_patterns": []
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize component health scores
        self._initialize_component_health()
    
    def update_maintenance_data(self, live_data: Dict[str, Any], mileage: int = None) -> None:
        """
        Update predictive maintenance analysis with live data
        
        Args:
            live_data: Current live data from OBD2 adapter
            mileage: Current vehicle mileage (if available)
        """
        if not live_data or 'data' not in live_data:
            return
        
        current_time = datetime.now()
        data = live_data['data']
        
        try:
            # Extract key maintenance-related parameters
            engine_temp = self._extract_engine_temperature(data)
            oil_temp = self._extract_oil_temperature(data)
            fuel_trims = self._extract_fuel_trims(data)
            misfire_data = self._extract_misfire_data(data)
            load_factor = self._extract_load_factor(data)
            rpm = self._extract_rpm(data)
            
            # Update mileage if provided
            if mileage:
                self.current_mileage = mileage
            
            # Create historical data point
            data_point = {
                'timestamp': current_time,
                'mileage': self.current_mileage,
                'engine_temp': engine_temp,
                'oil_temp': oil_temp,
                'fuel_trims': fuel_trims,
                'misfire_data': misfire_data,
                'load_factor': load_factor,
                'rpm': rpm,
                'driving_conditions': self._assess_driving_conditions(data)
            }
            
            with self._lock:
                # Store historical data
                self.historical_data.append(data_point)
                
                # Update component health scores
                self._update_component_health(data_point)
                
                # Analyze wear patterns
                self._analyze_wear_patterns(data_point)
                
                # Check for immediate alerts
                self._check_immediate_alerts(data_point)
                
                # Update predictive models
                self._update_predictive_models(data_point)
        
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Predictive maintenance update error: {e}")
    
    def update_dtc_patterns(self, dtcs: List[str]) -> None:
        """
        Update DTC pattern analysis
        
        Args:
            dtcs: List of current diagnostic trouble codes
        """
        if not dtcs:
            return
        
        current_time = datetime.now()
        
        with self._lock:
            for dtc in dtcs:
                self.dtc_patterns[dtc].append({
                    'timestamp': current_time,
                    'mileage': self.current_mileage,
                    'co_occurring_dtcs': [d for d in dtcs if d != dtc]
                })
                
                # Keep only recent patterns (last year)
                cutoff_date = current_time - timedelta(days=365)
                self.dtc_patterns[dtc] = [
                    pattern for pattern in self.dtc_patterns[dtc]
                    if pattern['timestamp'] > cutoff_date
                ]
    
    def get_maintenance_recommendations(self) -> Dict[str, Any]:
        """
        Get comprehensive maintenance recommendations
        
        Returns:
            Detailed maintenance analysis and recommendations
        """
        with self._lock:
            current_time = datetime.now()
            
            # Generate active alerts
            alerts = self._generate_maintenance_alerts()
            
            # Calculate component health summary
            health_summary = self._get_component_health_summary()
            
            # Predict upcoming maintenance
            upcoming_maintenance = self._predict_upcoming_maintenance()
            
            # Analyze driving patterns impact
            driving_impact = self._analyze_driving_patterns_impact()
            
            return {
                'timestamp': current_time.isoformat(),
                'vehicle_status': {
                    'current_mileage': self.current_mileage,
                    'overall_health_score': self._calculate_overall_health_score(),
                    'driving_conditions': self.driving_conditions,
                    'maintenance_due_soon': len([a for a in alerts if a.urgency in [MaintenanceUrgency.HIGH, MaintenanceUrgency.CRITICAL]])
                },
                'active_alerts': [asdict(alert) for alert in alerts],
                'component_health': health_summary,
                'upcoming_maintenance': upcoming_maintenance,
                'driving_impact_analysis': driving_impact,
                'bmw_specific_recommendations': self._get_bmw_specific_recommendations()
            }
    
    def get_oil_analysis(self) -> Dict[str, Any]:
        """
        Get detailed oil condition analysis
        
        Returns:
            Comprehensive oil analysis and change recommendations
        """
        with self._lock:
            if not self.historical_data:
                return {'error': 'Insufficient data for oil analysis'}
            
            # Analyze oil degradation patterns
            oil_data = self._extract_oil_analysis_data()
            
            if not oil_data:
                return {'error': 'No oil temperature data available'}
            
            # Calculate oil life estimate
            oil_life_estimate = self._calculate_oil_life_estimate(oil_data)
            
            # Assess driving conditions impact
            conditions_impact = self._assess_oil_conditions_impact()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'oil_life_analysis': {
                    'estimated_life_remaining_percent': oil_life_estimate['life_remaining'],
                    'estimated_miles_remaining': oil_life_estimate['miles_remaining'],
                    'recommended_change_date': oil_life_estimate['recommended_date'],
                    'confidence': oil_life_estimate['confidence']
                },
                'oil_condition_indicators': {
                    'average_operating_temp': oil_data['avg_temp'],
                    'high_temp_events': oil_data['high_temp_events'],
                    'thermal_stress_score': oil_data['thermal_stress'],
                    'contamination_risk': oil_data['contamination_risk']
                },
                'driving_conditions_impact': conditions_impact,
                'bmw_oil_recommendations': self._get_bmw_oil_recommendations()
            }
    
    def get_turbo_health_prediction(self) -> Dict[str, Any]:
        """
        Get turbo health prediction and maintenance forecast
        
        Returns:
            Detailed turbo health analysis and predictions
        """
        with self._lock:
            turbo_data = self._extract_turbo_health_data()
            
            if not turbo_data:
                return {'error': 'Insufficient turbo data for analysis'}
            
            # Predict turbo health degradation
            health_prediction = self._predict_turbo_health_degradation(turbo_data)
            
            # Identify failure precursors
            failure_precursors = self._identify_turbo_failure_precursors(turbo_data)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'current_turbo_health': {
                    'turbo1_health_score': health_prediction['turbo1_health'],
                    'turbo2_health_score': health_prediction['turbo2_health'],
                    'overall_turbo_health': health_prediction['overall_health'],
                    'degradation_rate': health_prediction['degradation_rate']
                },
                'health_prediction': {
                    'estimated_lifespan_miles': health_prediction['estimated_lifespan'],
                    'service_recommendation_miles': health_prediction['service_miles'],
                    'replacement_warning_miles': health_prediction['replacement_miles'],
                    'confidence': health_prediction['confidence']
                },
                'failure_precursors': failure_precursors,
                'maintenance_recommendations': self._get_turbo_maintenance_recommendations(health_prediction)
            }
    
    def get_dtc_pattern_analysis(self) -> Dict[str, Any]:
        """
        Get DTC pattern analysis and failure predictions
        
        Returns:
            DTC pattern analysis with predictive insights
        """
        with self._lock:
            if not self.dtc_patterns:
                return {'message': 'No DTC patterns recorded'}
            
            # Analyze DTC sequences and patterns
            pattern_analysis = self._analyze_dtc_sequences()
            
            # Predict potential failures
            failure_predictions = self._predict_failures_from_dtcs()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'dtc_pattern_summary': {
                    'total_unique_dtcs': len(self.dtc_patterns),
                    'most_frequent_dtcs': self._get_most_frequent_dtcs(),
                    'recent_dtc_trends': self._analyze_recent_dtc_trends()
                },
                'pattern_analysis': pattern_analysis,
                'failure_predictions': failure_predictions,
                'bmw_specific_insights': self._get_bmw_dtc_insights()
            }
    
    def record_maintenance_event(self, event_type: str, mileage: int = None, 
                                notes: str = None) -> None:
        """
        Record a maintenance event for pattern learning
        
        Args:
            event_type: Type of maintenance performed
            mileage: Mileage at which maintenance was performed
            notes: Additional notes about the maintenance
        """
        if mileage is None:
            mileage = self.current_mileage
        
        maintenance_event = {
            'timestamp': datetime.now(),
            'event_type': event_type,
            'mileage': mileage,
            'notes': notes
        }
        
        with self._lock:
            self.maintenance_history.append(maintenance_event)
            
            # Update component health based on maintenance
            self._update_health_from_maintenance(event_type, mileage)
            
            # Update last service mileage for specific services
            if event_type == "oil_change":
                self.last_oil_change_mileage = mileage
    
    def export_health_report(self, format_type: str = "json") -> str:
        """
        Export comprehensive health report
        
        Args:
            format_type: Export format ("json", "csv")
            
        Returns:
            Formatted health report
        """
        with self._lock:
            report_data = {
                'vehicle_summary': {
                    'current_mileage': self.current_mileage,
                    'overall_health_score': self._calculate_overall_health_score(),
                    'report_date': datetime.now().isoformat()
                },
                'component_health': {name: asdict(health) for name, health in self.component_health.items()},
                'maintenance_history': list(self.maintenance_history),
                'active_alerts': [asdict(alert) for alert in self._generate_maintenance_alerts()],
                'predictions': {
                    'oil_change': self._predict_next_oil_change(),
                    'major_service': self._predict_major_service(),
                    'component_replacements': self._predict_component_replacements()
                }
            }
            
            if format_type.lower() == "json":
                import json
                return json.dumps(report_data, indent=2, default=str)
            elif format_type.lower() == "csv":
                return self._export_csv_report(report_data)
            else:
                return str(report_data)
    
    # Private helper methods
    
    def _extract_engine_temperature(self, data: Dict[str, Any]) -> float:
        """Extract engine coolant temperature"""
        temp_data = data.get('COOLANT_TEMP', {})
        if isinstance(temp_data, dict) and 'value' in temp_data:
            return float(temp_data['value'])
        return 90.0  # Default operating temperature
    
    def _extract_oil_temperature(self, data: Dict[str, Any]) -> float:
        """Extract oil temperature (if available)"""
        # BMW-specific oil temperature PID
        oil_temp_data = data.get('OIL_TEMP', {})
        if isinstance(oil_temp_data, dict) and 'value' in oil_temp_data:
            return float(oil_temp_data['value'])
        
        # Estimate from engine temperature if oil temp not available
        engine_temp = self._extract_engine_temperature(data)
        return engine_temp + 10  # Oil typically runs 10°C hotter
    
    def _extract_fuel_trims(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract fuel trim data"""
        short_term_1 = data.get('SHORT_FUEL_TRIM_1', {}).get('value', 0.0)
        short_term_2 = data.get('SHORT_FUEL_TRIM_2', {}).get('value', 0.0)
        long_term_1 = data.get('LONG_FUEL_TRIM_1', {}).get('value', 0.0)
        long_term_2 = data.get('LONG_FUEL_TRIM_2', {}).get('value', 0.0)
        
        return {
            'short_term_1': float(short_term_1),
            'short_term_2': float(short_term_2),
            'long_term_1': float(long_term_1),
            'long_term_2': float(long_term_2)
        }
    
    def _extract_misfire_data(self, data: Dict[str, Any]) -> Dict[str, int]:
        """Extract misfire count data"""
        misfires = {}
        for i in range(1, 9):  # BMW N63 has 8 cylinders
            misfire_key = f'MISFIRE_CYLINDER_{i}'
            if misfire_key in data:
                misfires[f'cylinder_{i}'] = int(data[misfire_key].get('value', 0))
        
        return misfires
    
    def _extract_load_factor(self, data: Dict[str, Any]) -> float:
        """Extract engine load factor"""
        load_data = data.get('ENGINE_LOAD', {})
        if isinstance(load_data, dict) and 'value' in load_data:
            return float(load_data['value'])
        return 0.0
    
    def _extract_rpm(self, data: Dict[str, Any]) -> float:
        """Extract engine RPM"""
        rpm_data = data.get('RPM', {})
        if isinstance(rpm_data, dict) and 'value' in rpm_data:
            return float(rpm_data['value'])
        return 0.0
    
    def _assess_driving_conditions(self, data: Dict[str, Any]) -> str:
        """Assess current driving conditions"""
        load = self._extract_load_factor(data)
        rpm = self._extract_rpm(data)
        
        if load > 80 and rpm > 4000:
            return "severe"
        elif load > 60 or rpm > 3500:
            return "highway"
        elif rpm < 2000:
            return "city"
        else:
            return "normal"
    
    def _initialize_component_health(self) -> None:
        """Initialize component health scores"""
        components = [
            "engine_oil", "turbocharger_1", "turbocharger_2", "fuel_injectors",
            "spark_plugs", "air_filter", "fuel_filter", "cooling_system",
            "exhaust_system", "transmission", "brake_system", "suspension"
        ]
        
        for component in components:
            self.component_health[component] = ComponentHealthScore(
                component=component,
                health_score=100.0,
                health_status=ComponentHealth.EXCELLENT,
                wear_rate=0.0,
                confidence=0.5  # Initial low confidence
            )
    
    def _update_component_health(self, data_point: Dict[str, Any]) -> None:
        """Update component health scores based on data"""
        # Update oil health
        self._update_oil_health(data_point)
        
        # Update turbo health
        self._update_turbo_health(data_point)
        
        # Update injection system health
        self._update_injection_health(data_point)
        
        # Update cooling system health
        self._update_cooling_health(data_point)
    
    def _update_oil_health(self, data_point: Dict[str, Any]) -> None:
        """Update oil health score"""
        oil_health = self.component_health["engine_oil"]
        
        # Calculate degradation based on temperature and time
        oil_temp = data_point.get('oil_temp', 100)
        load_factor = data_point.get('load_factor', 50)
        
        # High temperature increases oil degradation
        temp_factor = max(1.0, (oil_temp - 100) / 50)  # Accelerated above 100°C
        load_factor_norm = load_factor / 100.0
        
        # Calculate degradation per data point (assuming 10Hz updates)
        degradation_per_second = (temp_factor * load_factor_norm * 0.001) / 3600  # Very small per second
        
        oil_health.health_score = max(0, oil_health.health_score - degradation_per_second)
        oil_health.wear_rate = temp_factor * load_factor_norm
        
        # Update health status
        if oil_health.health_score > 80:
            oil_health.health_status = ComponentHealth.EXCELLENT
        elif oil_health.health_score > 60:
            oil_health.health_status = ComponentHealth.GOOD
        elif oil_health.health_score > 40:
            oil_health.health_status = ComponentHealth.FAIR
        elif oil_health.health_score > 20:
            oil_health.health_status = ComponentHealth.POOR
        else:
            oil_health.health_status = ComponentHealth.CRITICAL
    
    def _update_turbo_health(self, data_point: Dict[str, Any]) -> None:
        """Update turbocharger health scores"""
        # This would integrate with turbo analytics module
        # For now, simulate based on temperature and load
        
        load_factor = data_point.get('load_factor', 50)
        engine_temp = data_point.get('engine_temp', 90)
        
        # High load and temperature stress turbos
        stress_factor = (load_factor / 100.0) * max(1.0, (engine_temp - 90) / 20)
        
        for turbo_name in ["turbocharger_1", "turbocharger_2"]:
            turbo_health = self.component_health[turbo_name]
            
            # Very gradual degradation
            degradation = stress_factor * 0.0001 / 3600  # Per second
            turbo_health.health_score = max(0, turbo_health.health_score - degradation)
            turbo_health.wear_rate = stress_factor
    
    def _update_injection_health(self, data_point: Dict[str, Any]) -> None:
        """Update fuel injection system health"""
        fuel_trims = data_point.get('fuel_trims', {})
        
        if fuel_trims:
            # Calculate average fuel trim deviation
            trim_values = list(fuel_trims.values())
            avg_deviation = statistics.mean([abs(trim) for trim in trim_values])
            
            # High fuel trim indicates injector problems
            injector_health = self.component_health["fuel_injectors"]
            
            if avg_deviation > 15:  # High deviation
                degradation = 0.001 / 3600  # Faster degradation
                injector_health.health_score = max(0, injector_health.health_score - degradation)
            
            injector_health.wear_rate = avg_deviation / 15.0  # Normalized wear rate
    
    def _update_cooling_health(self, data_point: Dict[str, Any]) -> None:
        """Update cooling system health"""
        engine_temp = data_point.get('engine_temp', 90)
        
        cooling_health = self.component_health["cooling_system"]
        
        # High temperatures indicate cooling system stress
        if engine_temp > 105:
            stress_factor = (engine_temp - 105) / 10
            degradation = stress_factor * 0.0005 / 3600
            cooling_health.health_score = max(0, cooling_health.health_score - degradation)
            cooling_health.wear_rate = stress_factor
    
    def _analyze_wear_patterns(self, data_point: Dict[str, Any]) -> None:
        """Analyze component wear patterns"""
        # Track patterns for predictive modeling
        pattern_key = data_point['driving_conditions']
        
        self.wear_patterns[pattern_key].append({
            'timestamp': data_point['timestamp'],
            'mileage': data_point['mileage'],
            'temperature_stress': data_point['engine_temp'] - 90,
            'load_stress': data_point['load_factor']
        })
        
        # Keep only recent patterns
        cutoff_date = datetime.now() - timedelta(days=30)
        self.wear_patterns[pattern_key] = [
            pattern for pattern in self.wear_patterns[pattern_key]
            if pattern['timestamp'] > cutoff_date
        ]
    
    def _check_immediate_alerts(self, data_point: Dict[str, Any]) -> None:
        """Check for immediate maintenance alerts"""
        # This would trigger alerts in real-time
        # For now, just log critical conditions
        
        if data_point['engine_temp'] > self.alert_thresholds['coolant_temp_celsius']:
            if self.logger:
                self.logger.warning(f"High coolant temperature: {data_point['engine_temp']}°C")
        
        # Check fuel trims
        fuel_trims = data_point.get('fuel_trims', {})
        for bank, trim in fuel_trims.items():
            if abs(trim) > self.alert_thresholds['fuel_trim_percent']:
                if self.logger:
                    self.logger.warning(f"High fuel trim {bank}: {trim}%")
    
    def _update_predictive_models(self, data_point: Dict[str, Any]) -> None:
        """Update predictive models with new data"""
        # Add data to pattern recognition models
        self.pattern_database["oil_degradation_patterns"].append({
            'oil_temp': data_point.get('oil_temp'),
            'load_factor': data_point.get('load_factor'),
            'driving_conditions': data_point.get('driving_conditions'),
            'timestamp': data_point['timestamp']
        })
        
        # Keep models to reasonable size
        for pattern_type in self.pattern_database:
            if len(self.pattern_database[pattern_type]) > 1000:
                self.pattern_database[pattern_type] = self.pattern_database[pattern_type][-1000:]
    
    def _generate_maintenance_alerts(self) -> List[MaintenanceAlert]:
        """Generate current maintenance alerts"""
        alerts = []
        
        # Oil change alert
        oil_health = self.component_health["engine_oil"]
        if oil_health.health_score < 30:
            alerts.append(MaintenanceAlert(
                component="engine_oil",
                alert_type="oil_change_due",
                urgency=MaintenanceUrgency.HIGH if oil_health.health_score < 15 else MaintenanceUrgency.MEDIUM,
                confidence=0.9,
                description=f"Engine oil condition is at {oil_health.health_score:.1f}%",
                recommendation="Schedule oil change within 500 miles",
                estimated_days_remaining=self._estimate_oil_change_days()
            ))
        
        # Turbo health alerts
        for turbo_name in ["turbocharger_1", "turbocharger_2"]:
            turbo_health = self.component_health[turbo_name]
            if turbo_health.health_score < 70:
                alerts.append(MaintenanceAlert(
                    component=turbo_name,
                    alert_type="turbo_service_recommended",
                    urgency=MaintenanceUrgency.MEDIUM,
                    confidence=0.7,
                    description=f"{turbo_name.replace('_', ' ').title()} health at {turbo_health.health_score:.1f}%",
                    recommendation="Consider turbocharger inspection and service"
                ))
        
        # Mileage-based alerts
        miles_since_oil_change = self.current_mileage - self.last_oil_change_mileage
        if miles_since_oil_change > self.bmw_maintenance_intervals["oil_change"] * 0.9:
            alerts.append(MaintenanceAlert(
                component="engine_oil",
                alert_type="mileage_based_service",
                urgency=MaintenanceUrgency.HIGH if miles_since_oil_change > self.bmw_maintenance_intervals["oil_change"] else MaintenanceUrgency.MEDIUM,
                confidence=1.0,
                description=f"Oil change due by mileage: {miles_since_oil_change} miles since last change",
                recommendation="Schedule BMW Condition Based Service oil change"
            ))
        
        return alerts
    
    def _get_component_health_summary(self) -> Dict[str, Any]:
        """Get summary of all component health scores"""
        summary = {}
        
        for component, health in self.component_health.items():
            summary[component] = {
                'health_score': round(health.health_score, 1),
                'health_status': health.health_status.value,
                'wear_rate': round(health.wear_rate, 3),
                'confidence': round(health.confidence, 2)
            }
        
        return summary
    
    def _predict_upcoming_maintenance(self) -> Dict[str, Any]:
        """Predict upcoming maintenance needs"""
        upcoming = {}
        
        # Oil change prediction
        oil_change_miles = self._predict_next_oil_change_mileage()
        upcoming["oil_change"] = {
            'estimated_mileage': oil_change_miles,
            'estimated_days': self._estimate_days_to_mileage(oil_change_miles),
            'type': 'condition_based'
        }
        
        # Major service intervals
        for service, interval in self.bmw_maintenance_intervals.items():
            if service != "oil_change":
                last_service_mileage = self._get_last_service_mileage(service)
                next_service_mileage = last_service_mileage + interval
                
                if next_service_mileage - self.current_mileage < interval * 0.2:  # Within 20% of interval
                    upcoming[service] = {
                        'estimated_mileage': next_service_mileage,
                        'estimated_days': self._estimate_days_to_mileage(next_service_mileage),
                        'type': 'scheduled_maintenance'
                    }
        
        return upcoming
    
    def _analyze_driving_patterns_impact(self) -> Dict[str, Any]:
        """Analyze impact of driving patterns on maintenance"""
        if not self.historical_data:
            return {'error': 'Insufficient driving data'}
        
        recent_data = list(self.historical_data)[-100:]  # Last 100 data points
        
        # Analyze driving condition distribution
        condition_counts = defaultdict(int)
        for data in recent_data:
            condition_counts[data.get('driving_conditions', 'normal')] += 1
        
        total_points = len(recent_data)
        condition_percentages = {
            condition: (count / total_points) * 100
            for condition, count in condition_counts.items()
        }
        
        # Calculate maintenance impact factor
        impact_factors = {
            'severe': 2.0,      # Severe driving doubles wear
            'highway': 0.8,     # Highway driving reduces wear
            'city': 1.2,        # City driving increases wear
            'normal': 1.0       # Normal driving baseline
        }
        
        weighted_impact = sum(
            (percentage / 100) * impact_factors.get(condition, 1.0)
            for condition, percentage in condition_percentages.items()
        )
        
        return {
            'driving_condition_distribution': condition_percentages,
            'maintenance_impact_factor': round(weighted_impact, 2),
            'recommendation': self._get_driving_pattern_recommendation(weighted_impact),
            'oil_change_adjustment': self._calculate_oil_change_adjustment(weighted_impact)
        }
    
    def _get_bmw_specific_recommendations(self) -> List[str]:
        """Get BMW-specific maintenance recommendations"""
        recommendations = []
        
        # BMW N63 specific recommendations
        if self.current_mileage > 30000:
            recommendations.append("Consider carbon cleaning for direct injection engine (N63)")
        
        if self.current_mileage > 40000:
            recommendations.append("Schedule walnut blasting for intake valve cleaning")
        
        # Turbo-specific recommendations
        turbo1_health = self.component_health["turbocharger_1"].health_score
        turbo2_health = self.component_health["turbocharger_2"].health_score
        
        if min(turbo1_health, turbo2_health) < 80:
            recommendations.append("Use BMW-approved synthetic oil for turbocharger protection")
            recommendations.append("Allow engine cool-down period before shutdown")
        
        # Check for severe driving conditions
        if self.driving_conditions == "severe":
            recommendations.append("Consider shortened oil change intervals for severe driving")
            recommendations.append("Monitor boost pressure and temperatures more frequently")
        
        return recommendations
    
    def _calculate_overall_health_score(self) -> float:
        """Calculate overall vehicle health score"""
        if not self.component_health:
            return 100.0
        
        # Weight components by importance
        component_weights = {
            "engine_oil": 0.3,
            "turbocharger_1": 0.15,
            "turbocharger_2": 0.15,
            "fuel_injectors": 0.1,
            "cooling_system": 0.1,
            "spark_plugs": 0.05,
            "air_filter": 0.05,
            "fuel_filter": 0.05,
            "exhaust_system": 0.05
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for component, health in self.component_health.items():
            weight = component_weights.get(component, 0.01)
            weighted_score += health.health_score * weight
            total_weight += weight
        
        return round(weighted_score / total_weight if total_weight > 0 else 100.0, 1)
    
    # Additional helper methods for specific analyses
    
    def _extract_oil_analysis_data(self) -> Optional[Dict[str, Any]]:
        """Extract oil-specific analysis data"""
        if not self.historical_data:
            return None
        
        recent_data = list(self.historical_data)[-500:]  # Last 500 points
        oil_temps = [data.get('oil_temp', 100) for data in recent_data]
        
        if not oil_temps:
            return None
        
        return {
            'avg_temp': statistics.mean(oil_temps),
            'max_temp': max(oil_temps),
            'high_temp_events': len([temp for temp in oil_temps if temp > 120]),
            'thermal_stress': statistics.mean([max(0, temp - 100) for temp in oil_temps]),
            'contamination_risk': self._assess_contamination_risk(recent_data)
        }
    
    def _calculate_oil_life_estimate(self, oil_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate remaining oil life"""
        current_health = self.component_health["engine_oil"].health_score
        
        # Estimate based on thermal stress and contamination
        thermal_factor = min(2.0, oil_data['thermal_stress'] / 20)  # Thermal stress factor
        contamination_factor = oil_data['contamination_risk']
        
        # Calculate degradation rate
        base_miles = self.bmw_maintenance_intervals["oil_change"]
        adjusted_miles = base_miles / (1 + thermal_factor + contamination_factor)
        
        miles_since_change = self.current_mileage - self.last_oil_change_mileage
        remaining_miles = max(0, adjusted_miles - miles_since_change)
        
        life_remaining = (remaining_miles / adjusted_miles) * 100 if adjusted_miles > 0 else 0
        
        return {
            'life_remaining': round(max(0, min(100, life_remaining)), 1),
            'miles_remaining': int(remaining_miles),
            'recommended_date': (datetime.now() + timedelta(days=self._estimate_days_to_mileage(remaining_miles))).isoformat(),
            'confidence': 0.8
        }
    
    def _assess_oil_conditions_impact(self) -> Dict[str, Any]:
        """Assess driving conditions impact on oil"""
        if not self.historical_data:
            return {'error': 'No data available'}
        
        recent_data = list(self.historical_data)[-200:]
        
        # Analyze conditions distribution
        conditions = [data.get('driving_conditions', 'normal') for data in recent_data]
        severe_percentage = (conditions.count('severe') / len(conditions)) * 100
        city_percentage = (conditions.count('city') / len(conditions)) * 100
        
        impact_assessment = "low"
        if severe_percentage > 30:
            impact_assessment = "high"
        elif severe_percentage > 15 or city_percentage > 60:
            impact_assessment = "medium"
        
        return {
            'severe_driving_percentage': round(severe_percentage, 1),
            'city_driving_percentage': round(city_percentage, 1),
            'impact_assessment': impact_assessment,
            'oil_change_recommendation': self._get_oil_change_recommendation(impact_assessment)
        }
    
    def _get_bmw_oil_recommendations(self) -> List[str]:
        """Get BMW-specific oil recommendations"""
        recommendations = [
            "Use BMW LongLife-01 FE or LL-14 FE+ approved oil",
            "BMW 0W-20 or 5W-30 viscosity for N63 engine",
            "Change oil filter with every oil change"
        ]
        
        turbo_health = min(
            self.component_health["turbocharger_1"].health_score,
            self.component_health["turbocharger_2"].health_score
        )
        
        if turbo_health < 90:
            recommendations.append("Consider high-quality synthetic oil for turbo protection")
            recommendations.append("Check for oil leaks around turbocharger seals")
        
        return recommendations
    
    def _assess_contamination_risk(self, data_points: List[Dict[str, Any]]) -> float:
        """Assess oil contamination risk from driving patterns"""
        if not data_points:
            return 0.0
        
        # Short trips increase contamination risk
        city_driving_count = sum(1 for data in data_points if data.get('driving_conditions') == 'city')
        contamination_risk = (city_driving_count / len(data_points)) * 0.5
        
        return min(1.0, contamination_risk)
    
    def _extract_turbo_health_data(self) -> Optional[Dict[str, Any]]:
        """Extract turbo-specific health data"""
        if not self.historical_data:
            return None
        
        recent_data = list(self.historical_data)[-300:]
        
        # Extract load and temperature patterns
        high_load_events = len([data for data in recent_data if data.get('load_factor', 0) > 80])
        avg_load = statistics.mean([data.get('load_factor', 0) for data in recent_data])
        
        return {
            'high_load_events': high_load_events,
            'avg_load_factor': avg_load,
            'turbo1_health': self.component_health["turbocharger_1"].health_score,
            'turbo2_health': self.component_health["turbocharger_2"].health_score,
            'data_points': len(recent_data)
        }
    
    def _predict_turbo_health_degradation(self, turbo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict turbo health degradation"""
        current_health = min(turbo_data['turbo1_health'], turbo_data['turbo2_health'])
        
        # Calculate degradation rate based on usage
        high_load_factor = turbo_data['high_load_events'] / turbo_data['data_points']
        degradation_rate = high_load_factor * 0.1  # 0.1% per high load event ratio
        
        # Estimate remaining lifespan
        remaining_health = current_health - 50  # Assume service needed at 50%
        estimated_lifespan_miles = (remaining_health / degradation_rate) * 1000 if degradation_rate > 0 else 100000
        
        return {
            'turbo1_health': turbo_data['turbo1_health'],
            'turbo2_health': turbo_data['turbo2_health'],
            'overall_health': current_health,
            'degradation_rate': round(degradation_rate, 4),
            'estimated_lifespan': int(min(200000, estimated_lifespan_miles)),
            'service_miles': self.current_mileage + int(estimated_lifespan_miles * 0.7),
            'replacement_miles': self.current_mileage + int(estimated_lifespan_miles),
            'confidence': 0.6
        }
    
    def _identify_turbo_failure_precursors(self, turbo_data: Dict[str, Any]) -> List[str]:
        """Identify potential turbo failure precursors"""
        precursors = []
        
        if turbo_data['turbo1_health'] < 70 or turbo_data['turbo2_health'] < 70:
            precursors.append("Low turbocharger health score detected")
        
        if turbo_data['high_load_events'] > turbo_data['data_points'] * 0.3:
            precursors.append("Excessive high-load operation detected")
        
        # Check historical patterns for specific warning signs
        if self.dtc_patterns:
            turbo_related_dtcs = ['P0299', 'P0234', 'P0235', 'P0236', 'P0237', 'P0238']
            for dtc in turbo_related_dtcs:
                if dtc in self.dtc_patterns and len(self.dtc_patterns[dtc]) > 2:
                    precursors.append(f"Recurring turbo-related DTC: {dtc}")
        
        return precursors
    
    def _get_turbo_maintenance_recommendations(self, health_prediction: Dict[str, Any]) -> List[str]:
        """Get turbo-specific maintenance recommendations"""
        recommendations = []
        
        if health_prediction['overall_health'] < 80:
            recommendations.append("Schedule turbocharger inspection")
            recommendations.append("Check boost pressure and vacuum lines")
            recommendations.append("Inspect turbocharger oil supply and return lines")
        
        if health_prediction['degradation_rate'] > 0.05:
            recommendations.append("Reduce high-load driving to preserve turbo life")
            recommendations.append("Allow proper engine cool-down after driving")
        
        recommendations.append("Use BMW LongLife oil specification for turbo protection")
        
        return recommendations
    
    def _analyze_dtc_sequences(self) -> Dict[str, Any]:
        """Analyze DTC occurrence sequences and patterns"""
        if not self.dtc_patterns:
            return {}
        
        sequence_analysis = {}
        
        for dtc, occurrences in self.dtc_patterns.items():
            if len(occurrences) > 1:
                # Analyze time patterns
                time_intervals = []
                for i in range(1, len(occurrences)):
                    interval = (occurrences[i]['timestamp'] - occurrences[i-1]['timestamp']).days
                    time_intervals.append(interval)
                
                if time_intervals:
                    sequence_analysis[dtc] = {
                        'occurrence_count': len(occurrences),
                        'avg_interval_days': round(statistics.mean(time_intervals), 1),
                        'pattern_type': self._classify_dtc_pattern(time_intervals),
                        'co_occurring_dtcs': self._find_co_occurring_dtcs(dtc)
                    }
        
        return sequence_analysis
    
    def _predict_failures_from_dtcs(self) -> List[Dict[str, Any]]:
        """Predict potential failures based on DTC patterns"""
        predictions = []
        
        # BMW-specific DTC failure patterns
        failure_patterns = {
            'P0299': {'component': 'turbocharger', 'confidence': 0.8, 'description': 'Turbo underboost condition'},
            'P0300': {'component': 'ignition_system', 'confidence': 0.9, 'description': 'Random misfire detected'},
            'P0171': {'component': 'fuel_system', 'confidence': 0.7, 'description': 'System too lean'},
            'P0087': {'component': 'fuel_pump', 'confidence': 0.8, 'description': 'Fuel rail pressure too low'}
        }
        
        for dtc, occurrences in self.dtc_patterns.items():
            if dtc in failure_patterns and len(occurrences) > 2:
                pattern = failure_patterns[dtc]
                
                # Calculate failure probability based on frequency
                recent_occurrences = [
                    occ for occ in occurrences 
                    if (datetime.now() - occ['timestamp']).days < 90
                ]
                
                if recent_occurrences:
                    failure_probability = min(0.9, len(recent_occurrences) * 0.2)
                    
                    predictions.append({
                        'component': pattern['component'],
                        'dtc': dtc,
                        'description': pattern['description'],
                        'failure_probability': round(failure_probability, 2),
                        'confidence': pattern['confidence'],
                        'recent_occurrences': len(recent_occurrences),
                        'recommendation': f"Inspect {pattern['component']} for potential failure"
                    })
        
        return predictions
    
    def _get_bmw_dtc_insights(self) -> List[str]:
        """Get BMW-specific DTC insights"""
        insights = []
        
        # Common BMW F13 DTC patterns
        common_dtcs = {
            'P0299': "Common in N63 engines - check wastegate and boost sensors",
            'P1014': "Valvetronic position sensor - BMW-specific system",
            'P0087': "High pressure fuel pump failure - common in direct injection BMW engines",
            'P0300': "Can be caused by carbon buildup in direct injection engines"
        }
        
        for dtc, occurrences in self.dtc_patterns.items():
            if dtc in common_dtcs and occurrences:
                insights.append(f"{dtc}: {common_dtcs[dtc]}")
        
        return insights
    
    def _classify_dtc_pattern(self, time_intervals: List[int]) -> str:
        """Classify DTC occurrence pattern"""
        if not time_intervals:
            return "single_occurrence"
        
        avg_interval = statistics.mean(time_intervals)
        interval_stdev = statistics.stdev(time_intervals) if len(time_intervals) > 1 else 0
        
        if avg_interval < 30:
            return "frequent"
        elif avg_interval < 90:
            return "periodic"
        elif interval_stdev < avg_interval * 0.3:
            return "regular"
        else:
            return "irregular"
    
    def _find_co_occurring_dtcs(self, target_dtc: str) -> List[str]:
        """Find DTCs that commonly occur with the target DTC"""
        co_occurring = defaultdict(int)
        
        if target_dtc in self.dtc_patterns:
            for occurrence in self.dtc_patterns[target_dtc]:
                for co_dtc in occurrence.get('co_occurring_dtcs', []):
                    co_occurring[co_dtc] += 1
        
        # Return DTCs that co-occur more than once
        return [dtc for dtc, count in co_occurring.items() if count > 1]
    
    def _update_health_from_maintenance(self, event_type: str, mileage: int) -> None:
        """Update component health based on maintenance performed"""
        maintenance_effects = {
            "oil_change": {"engine_oil": 100.0},
            "air_filter": {"air_filter": 100.0},
            "spark_plugs": {"spark_plugs": 100.0, "fuel_injectors": 95.0},
            "turbo_service": {"turbocharger_1": 95.0, "turbocharger_2": 95.0},
            "cooling_system": {"cooling_system": 100.0}
        }
        
        if event_type in maintenance_effects:
            for component, health_restoration in maintenance_effects[event_type].items():
                if component in self.component_health:
                    self.component_health[component].health_score = health_restoration
                    self.component_health[component].last_updated = datetime.now()
    
    def _predict_next_oil_change(self) -> Dict[str, Any]:
        """Predict next oil change"""
        oil_health = self.component_health["engine_oil"]
        
        # Estimate based on current degradation rate
        if oil_health.wear_rate > 0:
            remaining_health = oil_health.health_score - 20  # Change at 20%
            days_remaining = remaining_health / (oil_health.wear_rate * 24)  # Wear rate per hour
            
            return {
                'estimated_days': max(1, int(days_remaining)),
                'estimated_mileage': self.current_mileage + int(days_remaining * 50),  # Assume 50 miles/day
                'confidence': 0.7
            }
        
        # Fall back to mileage-based prediction
        miles_since_change = self.current_mileage - self.last_oil_change_mileage
        miles_remaining = self.bmw_maintenance_intervals["oil_change"] - miles_since_change
        
        return {
            'estimated_days': max(1, int(miles_remaining / 50)),
            'estimated_mileage': self.current_mileage + miles_remaining,
            'confidence': 0.9
        }
    
    def _predict_major_service(self) -> Dict[str, Any]:
        """Predict next major service interval"""
        # BMW typically has major services every 20,000-30,000 miles
        major_service_interval = 25000
        last_major_service = (self.current_mileage // major_service_interval) * major_service_interval
        next_major_service = last_major_service + major_service_interval
        
        return {
            'estimated_mileage': next_major_service,
            'estimated_days': self._estimate_days_to_mileage(next_major_service - self.current_mileage),
            'service_type': 'BMW Condition Based Service',
            'confidence': 0.95
        }
    
    def _predict_component_replacements(self) -> Dict[str, Dict[str, Any]]:
        """Predict when components will need replacement"""
        replacements = {}
        
        for component, health in self.component_health.items():
            if health.health_score < 80 and health.wear_rate > 0:
                # Estimate when health will reach critical level (20%)
                remaining_health = health.health_score - 20
                if health.wear_rate > 0:
                    days_to_replacement = remaining_health / (health.wear_rate * 24)
                    
                    replacements[component] = {
                        'estimated_days': max(30, int(days_to_replacement)),
                        'estimated_mileage': self.current_mileage + int(days_to_replacement * 50),
                        'current_health': round(health.health_score, 1),
                        'confidence': health.confidence
                    }
        
        return replacements
    
    def _predict_next_oil_change_mileage(self) -> int:
        """Predict mileage for next oil change"""
        base_interval = self.bmw_maintenance_intervals["oil_change"]
        
        # Adjust based on driving conditions
        adjustment_factor = 1.0
        if self.driving_conditions == "severe":
            adjustment_factor = 0.7
        elif self.driving_conditions == "city":
            adjustment_factor = 0.8
        elif self.driving_conditions == "highway":
            adjustment_factor = 1.2
        
        adjusted_interval = int(base_interval * adjustment_factor)
        return self.last_oil_change_mileage + adjusted_interval
    
    def _estimate_days_to_mileage(self, miles: int) -> int:
        """Estimate days to reach specific mileage"""
        if miles <= 0:
            return 0
        
        # Assume average daily driving
        daily_miles = 50  # Conservative estimate
        return max(1, int(miles / daily_miles))
    
    def _get_last_service_mileage(self, service_type: str) -> int:
        """Get mileage of last service for specific type"""
        # Look through maintenance history
        for event in reversed(self.maintenance_history):
            if event['event_type'] == service_type:
                return event['mileage']
        
        # If no history, estimate based on current mileage and service interval
        interval = self.bmw_maintenance_intervals.get(service_type, 10000)
        return (self.current_mileage // interval) * interval
    
    def _estimate_oil_change_days(self) -> int:
        """Estimate days until oil change needed"""
        oil_prediction = self._predict_next_oil_change()
        return oil_prediction.get('estimated_days', 30)
    
    def _get_driving_pattern_recommendation(self, impact_factor: float) -> str:
        """Get recommendation based on driving pattern impact"""
        if impact_factor > 1.5:
            return "Consider reducing severe driving conditions to extend component life"
        elif impact_factor > 1.2:
            return "Current driving patterns slightly increase maintenance needs"
        elif impact_factor < 0.9:
            return "Excellent driving patterns help extend maintenance intervals"
        else:
            return "Normal driving pattern impact on maintenance"
    
    def _calculate_oil_change_adjustment(self, impact_factor: float) -> str:
        """Calculate oil change interval adjustment"""
        if impact_factor > 1.5:
            return "Reduce oil change interval by 25-30%"
        elif impact_factor > 1.2:
            return "Reduce oil change interval by 10-15%"
        elif impact_factor < 0.9:
            return "May extend oil change interval by 10%"
        else:
            return "Follow standard BMW maintenance schedule"
    
    def _get_oil_change_recommendation(self, impact_assessment: str) -> str:
        """Get oil change recommendation based on impact assessment"""
        recommendations = {
            "high": "Change oil every 7,500 miles due to severe conditions",
            "medium": "Change oil every 8,500 miles due to mixed conditions", 
            "low": "Follow BMW 10,000 mile interval for normal conditions"
        }
        return recommendations.get(impact_assessment, "Follow BMW recommendations")
    
    def _get_most_frequent_dtcs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most frequently occurring DTCs"""
        dtc_counts = {
            dtc: len(occurrences) 
            for dtc, occurrences in self.dtc_patterns.items()
        }
        
        sorted_dtcs = sorted(dtc_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'dtc': dtc, 'occurrence_count': count}
            for dtc, count in sorted_dtcs[:limit]
        ]
    
    def _analyze_recent_dtc_trends(self) -> Dict[str, Any]:
        """Analyze recent DTC trends"""
        recent_cutoff = datetime.now() - timedelta(days=30)
        
        recent_dtc_count = 0
        for occurrences in self.dtc_patterns.values():
            recent_dtc_count += len([
                occ for occ in occurrences 
                if occ['timestamp'] > recent_cutoff
            ])
        
        # Simple trend analysis
        trend = "stable"
        if recent_dtc_count > 10:
            trend = "increasing"
        elif recent_dtc_count == 0:
            trend = "decreasing"
        
        return {
            'recent_dtc_count': recent_dtc_count,
            'trend': trend,
            'period_days': 30
        }
    
    def _export_csv_report(self, report_data: Dict[str, Any]) -> str:
        """Export health report in CSV format"""
        csv_lines = []
        
        # Header
        csv_lines.append("Component,Health Score,Health Status,Wear Rate,Confidence")
        
        # Component health data
        for component, health_data in report_data['component_health'].items():
            line = f"{component},{health_data['health_score']},{health_data['health_status']},{health_data['wear_rate']},{health_data['confidence']}"
            csv_lines.append(line)
        
        return "\n".join(csv_lines)