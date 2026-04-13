from adapters import ActionBase as BaseAction, ResultsBase as BaseResults
from typing import Dict, Any, Optional
import ctypes as ct
import threading
import numpy as np
import os
import json
###This class handles the actual calling of PILSS
class PILSSAction(BaseAction):
    def __init__(self, action_data, on_complete=None, case=None):
        self.DLL_Location_64bit = r"C:\\Program Files (x86)\\bin\\x64\\PILSS_DLL.dll"
        self.DLL_Location_32bit = r"C:\\Program Files (x86)\\bin\\x86\\PILSS_DLL.dll"
        
        # Helper function to handle empty/None values for numeric fields
        def get_numeric(key, default):
            try:
                value = action_data.get(key, default)
                if value == "" or value is None:
                    return default
                
                # Convert to the same type as default (int or float)
                if isinstance(default, int):
                    value = int(value)
                else:
                    value = float(value)
                
                # If default is non-zero and value is 0, use default to avoid division by zero
                if default != 0 and value == 0:
                    return default
                return value
            except Exception as e:
                raise ValueError(f"Error processing parameter '{key}': {str(e)}. Value provided: {repr(action_data.get(key))}")
        
        #Verify that DLLs exist
        action_data = super().correctActionData(action_data)

        if not os.path.isfile(self.DLL_Location_64bit):
            raise FileNotFoundError(f"64-bit DLL not found at {self.DLL_Location_64bit}")
        if not os.path.isfile(self.DLL_Location_32bit):
            raise FileNotFoundError(f"32-bit DLL not found at {self.DLL_Location_32bit}")
        
        self.caseName = action_data.get("caseName", "PILSS_Case")
        self.Version_number = get_numeric("Version_number", 2)
        self.bitness = get_numeric("bitness", 64)
        self.postproc = get_numeric("postproc", 2)

        # Cross section
        self.D_hydro = get_numeric("D_hydro", 0.4033)
        self.D = get_numeric("D", 0.4033)
        self.w_s = get_numeric("w_s", 484.76)
        self.w_s_i = get_numeric("w_s_i", 484.76)
        self.w_s_w = get_numeric("w_s_w", 484.76)
        self.m = get_numeric("m", 180.74)
        self.t_mgrt = get_numeric("t_mgrt", 0.0)
        self.k_lay_user = get_numeric("k_lay_user", 1.0)
        self.EI = get_numeric("EI", 0.0)
        self.T0 = get_numeric("T0", 0.0)
        self.alpha_m = get_numeric("alpha_m", 0.0)

        # Hydro parameters
        self.rho_w = get_numeric("rho_w", 1028.0)
        self.U_m = get_numeric("U_m", 0.0)
        self.T = get_numeric("T", 0.0)
        self.U_c = get_numeric("U_c", 0.358)
        self.Phi_t = get_numeric("Phi_t", 0.0)
        self.FH_m = get_numeric("FH_m", 0.0)
        self.depth = get_numeric("depth", 108.0)
        self.Tsim = get_numeric("Tsim", 10800)
        self.WaveVelRef_h = get_numeric("WaveVelRef_h", 0.20165)
        self.Hs = get_numeric("Hs", 14.3)
        self.Tp = get_numeric("Tp", 15.80)
        self.SpectrumPeakedness = get_numeric("SpectrumPeakedness", 3.30)
        self.theta_w = get_numeric("theta_w", 90.0)
        self.n_spreading = get_numeric("n_spreading", 8.0)
        self.r_H = get_numeric("r_H", 1.0)
        self.r_L = get_numeric("r_L", 1.0)
        self.HydroModel = get_numeric("HydroModel", 4)
        self.flowtype = get_numeric("flowtype", 1)
        self.roughness = get_numeric("roughness", 2)
        self.GenerateRegularWave = get_numeric("GenerateRegularWave", 2)
        self.SmoothWaveVelocity = get_numeric("SmoothWaveVelocity", 2)
        self.WaveOrder = get_numeric("WaveOrder", 1)
        self.SpectrumSpecification = get_numeric("SpectrumSpecification", 1)
        self.numseeds = get_numeric("numseeds", 5)
        self.HydrodynamicDiameter_int = get_numeric("HydrodynamicDiameter_int", 2)
        self.IncludeLiftReduction_int = get_numeric("IncludeLiftReduction_int", 2)

        # Seeds - handle both array and comma-separated string formats
        try:
            seedArray_phase_raw = action_data.get("seedArray_phase", [81663, 2142, 56225, 24849, 29681])
            if isinstance(seedArray_phase_raw, str):
                if seedArray_phase_raw.strip():
                    # Remove square brackets if present
                    seedArray_phase_raw = seedArray_phase_raw.strip().strip('[]')
                    seedArray_phase_raw = [int(x.strip()) for x in seedArray_phase_raw.split(',') if x.strip()]
                else:
                    seedArray_phase_raw = [81663, 2142, 56225, 24849, 29681]
            if not seedArray_phase_raw or (isinstance(seedArray_phase_raw, list) and len(seedArray_phase_raw) == 0):
                seedArray_phase_raw = [81663, 2142, 56225, 24849, 29681]
            self.seedArray_phase = np.require(np.array(seedArray_phase_raw), dtype=np.int32, requirements=['C'])
        except ValueError as e:
            raise ValueError(f"Error parsing 'seedArray_phase': {str(e)}. Input value: {repr(action_data.get('seedArray_phase'))}")
        except Exception as e:
            raise ValueError(f"Unexpected error with 'seedArray_phase': {str(e)}. Input value: {repr(action_data.get('seedArray_phase'))}")
        
        try:
            seedArray_crest_raw = action_data.get("seedArray_crest", [36657, 36657, 36657, 36657, 36657])
            if isinstance(seedArray_crest_raw, str):
                if seedArray_crest_raw.strip():
                    # Remove square brackets if present
                    seedArray_crest_raw = seedArray_crest_raw.strip().strip('[]')
                    seedArray_crest_raw = [int(x.strip()) for x in seedArray_crest_raw.split(',') if x.strip()]
                else:
                    seedArray_crest_raw = [36657, 36657, 36657, 36657, 36657]
            if not seedArray_crest_raw or (isinstance(seedArray_crest_raw, list) and len(seedArray_crest_raw) == 0):
                seedArray_crest_raw = [36657, 36657, 36657, 36657, 36657]
            self.seedArray_crest = np.require(np.array(seedArray_crest_raw), dtype=np.int32, requirements=['C'])
        except ValueError as e:
            raise ValueError(f"Error parsing 'seedArray_crest': {str(e)}. Input value: {repr(action_data.get('seedArray_crest'))}")
        except Exception as e:
            raise ValueError(f"Unexpected error with 'seedArray_crest': {str(e)}. Input value: {repr(action_data.get('seedArray_crest'))}")

        # Soil variables
        self.k_soil = get_numeric("k_soil", 65000.0)
        self.mu = get_numeric("mu", 0.6)
        self.gamma_mark = get_numeric("gamma_mark", 10212.0)
        self.rho_su = get_numeric("rho_su", 0.0)
        self.Nc = get_numeric("Nc", 0.0)
        self.su_z0 = get_numeric("su_z0", 0.0)
        self.delta_mobilization = get_numeric("delta_mobilization", 0.0)
        self.St = get_numeric("St", 1.0)
        self.alpha_soil = get_numeric("alpha_soil", 0.02)
        self.su_sigmav_NC = get_numeric("su_sigmav_NC", 0.0)
        self.alpha_brk = get_numeric("alpha_brk", 0.0)
        self.gamma_pre = get_numeric("gamma_pre", 0.0)
        self.m_OCR = get_numeric("m_OCR", 0.0)
        self.kappa_active = get_numeric("kappa_active", 0.0)
        self.kappa_passive = get_numeric("kappa_passive", 0.0)
        self.su_active = get_numeric("su_active", 0.0)
        self.su_passive = get_numeric("su_passive", 0.0)
        self.gamma_total = get_numeric("gamma_total", 0.0)
        self.su = get_numeric("su", 0.0)
        self.z_ini_user = get_numeric("z_ini_user", 0.0)
        self.z_t = get_numeric("z_t", 0.0)
        self.theta_t = get_numeric("theta_t", 0.0)
        self.SoilModel = get_numeric("SoilModel", 2)
        self.CalculatedLayFactor_int = get_numeric("CalculatedLayFactor_int", 2)
        self.UserDefinedLayFactor_int = get_numeric("UserDefinedLayFactor_int", 2)
        self.InitialPenetrationModel = get_numeric("InitialPenetrationModel", 1)
        self.remoulded_int = get_numeric("remoulded_int", 2)
        self.suction_int = get_numeric("suction_int", 2)
        self.waterFilled_int = get_numeric("waterFilled_int", 2)
        self.UserDefinedInitialPenetration_int = get_numeric("UserDefinedInitialPenetration_int", 2)
        self.IncludeTrench_int = get_numeric("IncludeTrench_int", 2)

        # Time series variables
        self.t_start = get_numeric("t_start", 0.0)
        self.delta_t = get_numeric("delta_t", 0.01)
        self.delta_t_signal = get_numeric("delta_t_signal", 0.35)
        self.delta_t_res = get_numeric("delta_t_res", 1.0)
        self.delta_t_plot = get_numeric("delta_t_plot", 1.0)

        # Dynamic solution variables
        self.RampUpPeriod = get_numeric("RampUpPeriod", 0.0)
        self.MaxNrOfIterations = get_numeric("MaxNrOfIterations", 10)
        self.RampUp_int = get_numeric("RampUp_int", 2)

        # Optionals
        self.printToFile = get_numeric("printToFile", 1)
        self.readWaveVelFromFile = get_numeric("readWaveVelFromFile", 2)
        self.generatePlots = action_data.get("generatePlots", False)
        self.ExplicitAcceleration = action_data.get("ExplicitAcceleration", True)
        super().__init__(action_data,on_complete,case)
        
        # Set file location for results storage - use case folder if available
        if case is not None and hasattr(case, 'resultsFolder'):
            self.fileLocation = case.resultsFolder
        else:
            # Fallback to a default location if no case is provided
            self.fileLocation = "results"

    def mySchema(self) -> Dict[str, Any]:
            schema = {
                "type": "object",
                
                # Schema profile definitions for different use cases
                "x-schema-profiles": {
                    "Minimal": ["caseName", "D", "U_c", "depth", "Tsim"],
                    "OnBottom": ["SoilModel","D","w_s","m", "H_s", "Tp","SpectrumPeakedness","U_c","t_mgrt", "depth","k_soil","mu","su","alpha_soil","numseeds", "seedArray_phase", "seedArray_crest"],
                    "Full": "all"
                },
                
                "properties": {
                    # General Settings
                    "caseName": {
                        "type": "string",
                        "title": "Case Name",
                        "description": "Identifier for this PILSS analysis case",
                        "x-Category": "General Settings",
                        "default": "PILSS_Case"
                    },
                    "Version_number": {
                        "type": "integer",
                        "title": "Version Number",
                        "description": "PILSS interface version (1=1.0, 2=2.2)",
                        "Options": {
                            "1.0": 1,
                            "2.2": 2
                        },
                        "x-Category": "General Settings",
                        "default": 2
                    },
                    "bitness": {
                        "type": "integer",
                        "title": "Bitness",
                        "description": "DLL architecture: 32 or 64-bit",
                        "Options": {
                            "64-Bit": 64,
                            "32-bit": 32
                        },
                        "x-Category": "General Settings",
                        "default": 64
                    },
                    "postproc": {
                        "type": "integer",
                        "title": "Post-processing",
                        "description": "Enable post-processing (1=yes, 2=no)",
                        "Options": {
                            "Yes": 1,
                            "No": 2
                        },
                        "x-Category": "General Settings",
                        "default": 2
                    },

                    # Cross Section Parameters
                    "D_hydro": {
                        "type": "number",
                        "title": "Hydrodynamic Diameter",
                        "description": "Hydrodynamic diameter for drag calculations",
                        "x-units": "m",
                        "x-Category": "Cross Section Parameters",
                        "default": 0.4033
                    },
                    "D": {
                        "type": "number",
                        "title": "Pipe Diameter",
                        "description": "Outer diameter of the pipeline",
                        "x-units": "m",
                        "x-Category": "Cross Section Parameters",
                        "default": 0.4033
                    },
                    "w_s": {
                        "type": "number",
                        "title": "Submerged Weight",
                        "description": "Submerged weight per unit length",
                        "x-units": "N/m",
                        "x-Category": "Cross Section Parameters",
                        "default": 484.76
                    },
                    "w_s_i": {
                        "type": "number",
                        "title": "Submerged Weight (Installation)",
                        "description": "Submerged weight per unit length (installation condition)",
                        "x-units": "N/m",
                        "x-Category": "Cross Section Parameters",
                        "default": 484.76
                    },
                    "w_s_w": {
                        "type": "number",
                        "title": "Submerged Weight (Waterfilled)",
                        "description": "Submerged weight per unit length in water-filled condition",
                        "x-units": "N/m",
                        "x-Category": "Cross Section Parameters",
                        "default": 484.76
                    },
                    "m": {
                        "type": "number",
                        "title": "Mass per Unit Length",
                        "description": "Total mass per unit length of pipe",
                        "x-units": "kg/m",
                        "x-Category": "Cross Section Parameters",
                        "default": 180.74
                    },
                    "t_mgrt": {
                        "type": "number",
                        "title": "Marine Growth Thickness",
                        "description": "Thickness of marine growth on the pipe",
                        "x-units": "m",
                        "x-Category": "Cross Section Parameters",
                        "default": 0.0
                    },
                    "k_lay_user": {
                        "type": "number",
                        "title": "Lay Factor",
                        "description": "User-defined lay tension factor",
                        "x-Category": "Cross Section Parameters",
                        "default": 1.0
                    },
                    "EI": {
                        "type": "number",
                        "title": "Bending Stiffness",
                        "description": "Flexural rigidity of the pipeline",
                        "x-units": "N·m²",
                        "x-Category": "Cross Section Parameters",
                        "default": 0.0
                    },
                    "T0": {
                        "type": "number",
                        "title": "Lay Tension (Horizontal)",
                        "description": "Lay tension — horizontal component",
                        "x-units": "N",
                        "x-Category": "Cross Section Parameters",
                        "default": 0.0
                    },
                    "alpha_m": {
                        "type": "number",
                        "title": "Mass Coefficient Alpha",
                        "description": "Mass coefficient for dynamic analysis",
                        "x-Category": "Cross Section Parameters",
                        "default": 0.0
                    },

                    # Hydrodynamic Parameters
                    "rho_w": {
                        "type": "number",
                        "title": "Water Density",
                        "description": "Density of seawater",
                        "x-units": "kg/m³",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 1028.0
                    },
                    "U_m": {
                        "type": "number",
                        "title": "Flow Velocity Amplitude",
                        "description": "Flow velocity amplitude (used for regular waves)",
                        "x-units": "m/s",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 0.0
                    },
                    "T": {
                        "type": "number",
                        "title": "Wave Period",
                        "description": "Wave period for regular waves",
                        "x-units": "s",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 0.0
                    },
                    "U_c": {
                        "type": "number",
                        "title": "Current Velocity",
                        "description": "Steady current velocity at reference height",
                        "x-units": "m/s",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 0.358
                    },
                    "Phi_t": {
                        "type": "number",
                        "title": "Phase Angle",
                        "description": "Phase angle for wave analysis",
                        "x-units": "deg",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 0.0
                    },
                    "FH_m": {
                        "type": "number",
                        "title": "Mean Horizontal Force",
                        "description": "Mean horizontal hydrodynamic force",
                        "x-units": "N/m",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 0.0
                    },
                    "depth": {
                        "type": "number",
                        "title": "Water Depth",
                        "description": "Water depth at site",
                        "x-units": "m",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 108.0
                    },
                    "Tsim": {
                        "type": "integer",
                        "title": "Simulation Duration",
                        "description": "Total simulation time",
                        "x-units": "s",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 10800
                    },
                    "WaveVelRef_h": {
                        "type": "number",
                        "title": "Wave Velocity Reference Height",
                        "description": "Reference height for wave velocity calculations",
                        "x-units": "m",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 0.20165
                    },
                    "Hs": {
                        "type": "number",
                        "title": "Significant Wave Height",
                        "description": "Significant wave height (H_s or H_1/3)",
                        "x-units": "m",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 14.3
                    },
                    "Tp": {
                        "type": "number",
                        "title": "Peak Period",
                        "description": "Spectral peak period",
                        "x-units": "s",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 15.80
                    },
                    "SpectrumPeakedness": {
                        "type": "number",
                        "title": "Spectrum Peakedness",
                        "description": "Peakedness parameter (gamma) for JONSWAP spectrum",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 3.30
                    },
                    "theta_w": {
                        "type": "number",
                        "title": "Wave Direction",
                        "description": "Mean wave direction relative to pipeline",
                        "x-units": "deg",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 90.0
                    },
                    "n_spreading": {
                        "type": "number",
                        "title": "Directional Spreading",
                        "description": "Directional spreading exponent",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 8.0
                    },
                    "r_H": {
                        "type": "number",
                        "title": "High-Frequency Factor",
                        "description": "High-frequency reduction factor",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 1.0
                    },
                    "r_L": {
                        "type": "number",
                        "title": "Low-Frequency Factor",
                        "description": "Low-frequency reduction factor",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 1.0
                    },
                    "HydroModel": {
                        "type": "integer",
                        "title": "Hydrodynamic Model",
                        "description": "Hydrodynamic model selection (1-5)",
                        "Options": {
                            "Model 1": 1,
                            "Model 2": 2,
                            "Model 3": 3,
                            "Database (4)": 4,
                            "Horizontal Sine (5)": 5
                        },
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 4
                    },
                    "flowtype": {
                        "type": "integer",
                        "title": "Flow Type",
                        "description": "Flow type: 1=steady, 2=oscillatory, 3=combined",
                        "Options": {
                            "Steady": 1,
                            "Oscillatory": 2,
                            "Combined": 3
                        },
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 1
                    },
                    "roughness": {
                        "type": "integer",
                        "title": "Roughness Model",
                        "description": "Surface roughness model selection",
                        "Options": {
                            "Smooth (1)": 1,
                            "Rough (2)": 2,
                            "Very Rough (3)": 3
                        },
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 2
                    },
                    "GenerateRegularWave": {
                        "type": "integer",
                        "title": "Generate Regular Wave",
                        "description": "Use regular waves (1=yes, 2=no)",
                        "Options": {
                            "Regular (1)": 1,
                            "Irregular (2)": 2
                        },
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 2
                    },
                    "SmoothWaveVelocity": {
                        "type": "integer",
                        "title": "Smooth Wave Velocity",
                        "description": "Apply velocity smoothing (1=yes, 2=no)",
                        "Options": {
                            "Yes (1)": 1,
                            "No (2)": 2
                        },
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 2
                    },
                    "WaveOrder": {
                        "type": "integer",
                        "title": "Wave Order",
                        "description": "Wave theory order: 1=linear, 2=2nd order",
                        "Options": {
                            "Linear (1)": 1,
                            "Second Order (2)": 2
                        },
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 1
                    },
                    "SpectrumSpecification": {
                        "type": "integer",
                        "title": "Spectrum Specification",
                        "description": "Wave spectrum type (1=JONSWAP, 2=PM, etc.)",
                        "Options": {
                            "JONSWAP (1)": 1,
                            "PM (2)": 2,
                            "Other (3)": 3
                        },
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 1
                    },
                    "numseeds": {
                        "type": "integer",
                        "title": "Number of Seeds",
                        "description": "Number of random phase realizations",
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 5
                    },
                    "HydrodynamicDiameter_int": {
                        "type": "integer",
                        "title": "Use Hydrodynamic Diameter",
                        "description": "Use hydrodynamic diameter (1=yes, 2=no)",
                        "Options": {
                            "Yes": 1,
                            "No": 2
                        },
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 2
                    },
                    "IncludeLiftReduction_int": {
                        "type": "integer",
                        "title": "Include Lift Reduction",
                        "description": "Include lift reduction factor (1=yes, 2=no)",
                        "Options": {
                            "Yes": 1,
                            "No": 2
                        },
                        "x-Category": "Hydrodynamic Parameters",
                        "default": 2
                    },

                    # Random Seeds
                    "seedArray_phase": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "title": "Phase Seeds",
                        "description": "Random seeds for wave phase generation",
                        "x-Category": "Random Seeds",
                        "default": [81663, 2142, 56225, 24849, 29681]
                    },
                    "seedArray_crest": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "title": "Crest Seeds",
                        "description": "Random seeds for wave crest generation",
                        "x-Category": "Random Seeds",
                        "default": [36657, 36657, 36657, 36657, 36657]
                    },

                    # Soil Parameters
                    "k_soil": {
                        "type": "number",
                        "title": "Soil Stiffness",
                        "description": "Elastic stiffness of the soil (recommended ~65000 N/m/m)",
                        "x-units": "N/m/m",
                        "x-Category": "Soil Parameters",
                        "default": 65000.0
                    },
                    "mu": {
                        "type": "number",
                        "title": "Friction Coefficient",
                        "description": "Pipe-soil friction coefficient",
                        "x-Category": "Soil Parameters",
                        "default": 0.6
                    },
                    "gamma_mark": {
                        "type": "number",
                        "title": "Submerged Soil Unit Weight",
                        "description": "Submerged unit weight of soil",
                        "x-units": "N/m³",
                        "x-Category": "Soil Parameters",
                        "default": 10212.0
                    },
                    "rho_su": {
                        "type": "number",
                        "title": "Undrained Shear Strength Gradient",
                        "description": "Gradient of undrained shear strength with depth",
                        "x-units": "kPa/m",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "Nc": {
                        "type": "number",
                        "title": "Bearing Capacity Factor",
                        "description": "Bearing capacity factor for soil",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "su_z0": {
                        "type": "number",
                        "title": "Surface Undrained Shear Strength",
                        "description": "Undrained shear strength at mudline",
                        "x-units": "kPa",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "delta_mobilization": {
                        "type": "number",
                        "title": "Mobilization Distance",
                        "description": "Mobilization distance expressed as fraction of pipe-soil contact width B (dimensionless)",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "St": {
                        "type": "number",
                        "title": "Sensitivity",
                        "description": "Soil sensitivity (remoulded strength ratio)",
                        "x-Category": "Soil Parameters",
                        "default": 1.0
                    },
                    "alpha_soil": {
                        "type": "number",
                        "title": "Soil Alpha",
                        "description": "Soil parameter alpha",
                        "x-Category": "Soil Parameters",
                        "default": 0.02
                    },
                    "su_sigmav_NC": {
                        "type": "number",
                        "title": "Normalized Shear Strength (NC)",
                        "description": "Normalized undrained shear strength for normally consolidated soil",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "alpha_brk": {
                        "type": "number",
                        "title": "Breakout Alpha",
                        "description": "Alpha factor for breakout calculation",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "gamma_pre": {
                        "type": "number",
                        "title": "Preconsolidation Unit Weight",
                        "description": "Unit weight for preconsolidation calculation",
                        "x-units": "N/m³",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "m_OCR": {
                        "type": "number",
                        "title": "OCR Exponent",
                        "description": "Exponent for overconsolidation ratio calculation",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "kappa_active": {
                        "type": "number",
                        "title": "Active Earth Pressure Coefficient",
                        "description": "Active lateral earth pressure coefficient",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "kappa_passive": {
                        "type": "number",
                        "title": "Passive Earth Pressure Coefficient",
                        "description": "Passive lateral earth pressure coefficient",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "su_active": {
                        "type": "number",
                        "title": "Active Shear Strength",
                        "description": "Undrained shear strength for active case",
                        "x-units": "kPa",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "su_passive": {
                        "type": "number",
                        "title": "Passive Shear Strength",
                        "description": "Undrained shear strength for passive case",
                        "x-units": "kPa",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "gamma_total": {
                        "type": "number",
                        "title": "Total Soil Unit Weight",
                        "description": "Total unit weight of soil",
                        "x-units": "N/m³",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "su": {
                        "type": "number",
                        "title": "Undrained Shear Strength",
                        "description": "Constant undrained shear strength",
                        "x-units": "kPa",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "z_ini_user": {
                        "type": "number",
                        "title": "Initial Penetration (User)",
                        "description": "User-defined initial penetration depth",
                        "x-units": "m",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "z_t": {
                        "type": "number",
                        "title": "Trench Depth",
                        "description": "Depth of seabed trench",
                        "x-units": "m",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "theta_t": {
                        "type": "number",
                        "title": "Trench Angle",
                        "description": "Side slope angle of trench",
                        "x-units": "deg",
                        "x-Category": "Soil Parameters",
                        "default": 0.0
                    },
                    "SoilModel": {
                        "type": "integer",
                        "title": "Soil Model",
                        "description": "Soil model selection (1=Coulomb, 2=Pipe-sand, 3=Pipe-clay)",
                        "Options": {
                            "Coulomb (1)": 1,
                            "Pipe-sand (2)": 2,
                            "Pipe-clay (3)": 3
                        },
                        "x-Category": "Soil Parameters",
                        "default": 2
                    },
                    "CalculatedLayFactor_int": {
                        "type": "integer",
                        "title": "Calculate Lay Factor",
                        "description": "Calculate lay factor automatically (1=yes, 2=no)",
                        "Options": {"Yes": 1, "No": 2},
                        "x-Category": "Soil Parameters",
                        "default": 2
                    },
                    "UserDefinedLayFactor_int": {
                        "type": "integer",
                        "title": "User-Defined Lay Factor",
                        "description": "Use user-defined lay factor (1=yes, 2=no)",
                        "Options": {"Yes": 1, "No": 2},
                        "x-Category": "Soil Parameters",
                        "default": 2
                    },
                    "InitialPenetrationModel": {
                        "type": "integer",
                        "title": "Initial Penetration Model",
                        "description": "Model for initial penetration (1=Verley & Lund, 2=SAFEBUCK, 3=Geotechnical)",
                        "Options": {"Verley & Lund (1)": 1, "SAFEBUCK (2)": 2, "Geotechnical (3)": 3},
                        "x-Category": "Soil Parameters",
                        "default": 1
                    },
                    "remoulded_int": {
                        "type": "integer",
                        "title": "Include Remoulding",
                        "description": "Account for soil remoulding (1=yes, 2=no)",
                        "Options": {"Yes": 1, "No": 2},
                        "x-Category": "Soil Parameters",
                        "default": 2
                    },
                    "suction_int": {
                        "type": "integer",
                        "title": "Include Suction",
                        "description": "Include suction forces (1=yes, 2=no)",
                        "Options": {"Yes": 1, "No": 2},
                        "x-Category": "Soil Parameters",
                        "default": 2
                    },
                    "waterFilled_int": {
                        "type": "integer",
                        "title": "Water-Filled Pipe",
                        "description": "Pipe is water-filled (1=yes, 2=no)",
                        "Options": {"Yes": 1, "No": 2},
                        "x-Category": "Soil Parameters",
                        "default": 2
                    },
                    "UserDefinedInitialPenetration_int": {
                        "type": "integer",
                        "title": "User-Defined Initial Penetration",
                        "description": "Use user-defined initial penetration (1=yes, 2=no)",
                        "Options": {"Yes": 1, "No": 2},
                        "x-Category": "Soil Parameters",
                        "default": 2
                    },
                    "IncludeTrench_int": {
                        "type": "integer",
                        "title": "Include Trench",
                        "description": "Include seabed trench (1=yes, 2=no)",
                        "Options": {"Yes": 1, "No": 2},
                        "x-Category": "Soil Parameters",
                        "default": 2
                    },

                    # Time Series Parameters
                    "t_start": {
                        "type": "number",
                        "title": "Start Time",
                        "description": "Simulation start time",
                        "x-units": "s",
                        "x-Category": "Time Series Parameters",
                        "default": 0.0
                    },
                    "delta_t": {
                        "type": "number",
                        "title": "Time Step",
                        "description": "Time step for main simulation",
                        "x-units": "s",
                        "x-Category": "Time Series Parameters",
                        "default": 0.01
                    },
                    "delta_t_signal": {
                        "type": "number",
                        "title": "Signal Time Step",
                        "description": "Time step for signal output",
                        "x-units": "s",
                        "x-Category": "Time Series Parameters",
                        "default": 0.35
                    },
                    "delta_t_res": {
                        "type": "number",
                        "title": "Results Time Step",
                        "description": "Time step for results output",
                        "x-units": "s",
                        "x-Category": "Time Series Parameters",
                        "default": 1.0
                    },
                    "delta_t_plot": {
                        "type": "number",
                        "title": "Plot Time Step",
                        "description": "Time step for plot data output",
                        "x-units": "s",
                        "x-Category": "Time Series Parameters",
                        "default": 1.0
                    },

                    # Dynamic Solution Parameters
                    "RampUpPeriod": {
                        "type": "number",
                        "title": "Ramp-Up Period",
                        "description": "Duration of force ramp-up at start",
                        "x-units": "s",
                        "x-Category": "Dynamic Solution Parameters",
                        "default": 0.0
                    },
                    "MaxNrOfIterations": {
                        "type": "integer",
                        "title": "Max Iterations",
                        "description": "Maximum number of iterations per time step",
                        "x-Category": "Dynamic Solution Parameters",
                        "default": 10
                    },
                    "RampUp_int": {
                        "type": "integer",
                        "title": "Enable Ramp-Up",
                        "description": "Enable ramp-up (1=yes, 2=no)",
                        "Options": {"Yes": 1, "No": 2},
                        "x-Category": "Dynamic Solution Parameters",
                        "default": 2
                    },

                    # Output Options
                    "printToFile": {
                        "type": "integer",
                        "title": "Print to File",
                        "description": "Output level: 1=all, 2=none, 3=summary only",
                        "Options": {
                            "All (1)": 1,
                            "None (2)": 2,
                            "Summary Only (3)": 3
                        },
                        "x-Category": "Output Options",
                        "default": 1
                    },
                    "readWaveVelFromFile": {
                        "type": "integer",
                        "title": "Read Wave Velocity from File",
                        "description": "Read wave velocities from file (1=yes, 2=no)",
                        "Options": {"Yes": 1, "No": 2},
                        "x-Category": "Output Options",
                        "default": 2
                    },
                    "generatePlots": {
                        "type": "boolean",
                        "title": "Generate Plots",
                        "description": "Generate result plots",
                        "x-Category": "Output Options",
                        "default": False
                    },
                    "ExplicitAcceleration": {
                        "type": "boolean",
                        "title": "Explicit Acceleration",
                        "description": "Use explicit acceleration calculation",
                        "Options": {"Yes": True, "No": False},
                        "x-Category": "Output Options",
                        "default": True
                    }
                },
                "required": []
            }
            return schema

    def perform_action(self) -> Dict[str, Any]:
            def create_fortran_string_buffer(py_string):
                MAX_STR_LEN = 4096
                try:
                    byte_string = py_string.encode('utf-8')
                    if len(byte_string) >= MAX_STR_LEN:
                        raise ValueError(f"String is too long for Fortran buffer (max {MAX_STR_LEN} bytes). String length: {len(byte_string)} bytes. String value: {py_string[:100]}...")
                    padded_string = byte_string.ljust(MAX_STR_LEN, b' ')
                    return ct.create_string_buffer(padded_string, MAX_STR_LEN)
                except Exception as e:
                    raise ValueError(f"Error creating Fortran string buffer for value '{py_string}': {str(e)}") from e
    
            def run_PILSS_interfacev1(inCross_real, inHydro_real, inHydro_int, seedArray_phase, seedArray_crest,
                                    inSoil_real, inSoil_int, inTime_real, inTime_int,
                                    delta_t, delta_t_signal, delta_t_res, delta_t_plot,
                                    Tsimulation, numseeds, printToFile, readWaveVelFromFile,
                                    generatePlots, ExplicitAcceleration):

                # Loading the .DLL
                try:
                    if self.bitness == 64:
                        fortlib = ct.CDLL(self.DLL_Location_64bit)
                    else:
                        fortlib = ct.CDLL(self.DLL_Location_32bit)
                except OSError as e:
                    dll_path = self.DLL_Location_64bit if self.bitness == 64 else self.DLL_Location_32bit
                    raise OSError(f"Failed to load {self.bitness}-bit DLL from '{dll_path}'. Error: {str(e)}") from e
                except Exception as e:
                    raise RuntimeError(f"Unexpected error loading DLL (bitness={self.bitness}): {str(e)}") from e
                # Specify input array properties
                fortlib.PILSSInterface.argtypes = [
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # inCross_real
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # inHydro_real
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # inHydro_int
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # seedArray_phase
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # seedArray_crests
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # inSoil_real
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # inSoil_int
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # inTime_real
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # inTime_int
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # NrOfTimesteps
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # NrOfTimesteps_signal
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # NrOfTimesteps_res
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # inDyn_real
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # inDyn_int
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # t_vector_U
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # U_t_matrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # A_t_matrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # F_H_matrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # F_L_matrix
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # NrOfPlotsteps
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # addedPlotRows
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=0, flags='C_CONTIGUOUS'),  # delta_t_plot
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # stepLength
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # printToFile
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # readWaveVelFromFile
                    np.ctypeslib.ndpointer(dtype=bool, ndim=0, flags='C_CONTIGUOUS'),  # generatePlots
                    np.ctypeslib.ndpointer(dtype=bool, ndim=0, flags='C_CONTIGUOUS'),  # ExplicitAcceleration
                    np.ctypeslib.ndpointer(dtype=bool, ndim=0, flags='C_CONTIGUOUS'),  # dummyBoolean1
                    np.ctypeslib.ndpointer(dtype=bool, ndim=0, flags='C_CONTIGUOUS'),  # dummyBoolean2
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # result_matrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # maxMatrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # minMatrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # maxAbsMatrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # t_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # y_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # z_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # v_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # a_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # Fsoil_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # Fstiff_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # FHrel_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # FLrel_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # yref_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='C_CONTIGUOUS'),    # iElPl_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='C_CONTIGUOUS')     # outVar_int_matrix
                ]

                # Example of input arrays/values/bools which are passed onto Fortran
                inDyn_real = np.require(np.zeros(numseeds), dtype=np.float64, requirements=['C'])
                inDyn_int = np.require(np.array([10.0, 2.0]), dtype=np.int32, requirements=['C'])

                # Validate time step parameters
                if delta_t <= 0:
                    raise ValueError(f"delta_t must be greater than 0. Current value: {delta_t}")
                if delta_t_signal <= 0:
                    raise ValueError(f"delta_t_signal must be greater than 0. Current value: {delta_t_signal}")
                if delta_t_res <= 0:
                    raise ValueError(f"delta_t_res must be greater than 0. Current value: {delta_t_res}")
                if delta_t_plot <= 0:
                    raise ValueError(f"delta_t_plot must be greater than 0. Current value: {delta_t_plot}")
                if Tsimulation <= 0:
                    raise ValueError(f"Tsimulation must be greater than 0. Current value: {Tsimulation}")

                # Time steps
                try:
                    NrOfTimesteps = np.require((np.ceil(Tsimulation / delta_t) + 1), dtype=np.int32, requirements=['C'])
                    NrOfTimesteps_signal = np.require((np.ceil(Tsimulation / delta_t_signal) + 1), dtype=np.int32, requirements=['C'])
                    NrOfTimesteps_res = np.require((np.ceil(Tsimulation / delta_t_res) + 1), dtype=np.int32, requirements=['C'])
                    NrOfPlotsteps = np.require((np.ceil(Tsimulation / delta_t_plot) + 1), dtype=np.int32, requirements=['C'])
                except ZeroDivisionError as e:
                    raise ValueError(f"Division by zero in time step calculation. Tsimulation={Tsimulation}, delta_t={delta_t}, delta_t_signal={delta_t_signal}, delta_t_res={delta_t_res}, delta_t_plot={delta_t_plot}") from e
                t_vector_U = np.require(np.zeros(NrOfTimesteps_signal), dtype=np.float64, requirements=['C'])

                # Results
                U_t_matrix = np.require(np.zeros((numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                A_t_matrix = np.require(np.zeros((numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                F_H_matrix = np.require(np.zeros((numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                F_L_matrix = np.require(np.zeros((numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                result_matrix = np.require(np.zeros((6, 2)), dtype=np.float64, requirements=['C'])
                maxMatrix = np.require(np.zeros((numseeds, 10)), dtype=np.float64, requirements=['C'])
                minMatrix = np.require(np.zeros((numseeds, 10)), dtype=np.float64, requirements=['C'])
                maxAbsMatrix = np.require(np.zeros((numseeds, 10)), dtype=np.float64, requirements=['C'])

                # Plot
                addedPlotRows = 0 if NrOfPlotsteps % 1 == 0 else 1
                if NrOfPlotsteps % 1 == 0:
                    addedPlotRows = np.require(0, dtype=np.int32, requirements=['C'])
                else:
                    addedPlotRows = np.require(1, dtype=np.int32, requirements=['C'])

                t_matrix_plot = np.require(np.zeros((1, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                y_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                z_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                v_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                a_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                Fsoil_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                Fstiff_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                FHrel_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                FLrel_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                yref_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                iElPl_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps), dtype=np.int32), requirements=['C'])
                outvar_int_matrix = np.require(np.zeros((numseeds, 5), dtype=np.int32), requirements=['C'])
                dummyInteger = np.require(1, dtype=np.int32, requirements=['C'])
                dummyBoolean = np.require(False, dtype=bool, requirements=['C'])
                dummyBoolean2 = np.require(True, dtype=bool, requirements=['C'])
                legacyApi = False

                # Call the Fortran function
                try:
                    res = fortlib.PILSSInterface(inCross_real, inHydro_real, inHydro_int, seedArray_phase, seedArray_crest,
                                                inSoil_real, inSoil_int, inTime_real, inTime_int,
                                                NrOfTimesteps, NrOfTimesteps_signal, NrOfTimesteps_res,
                                                inDyn_real, inDyn_int, t_vector_U,
                                                U_t_matrix, A_t_matrix, F_H_matrix, F_L_matrix,
                                                NrOfPlotsteps, addedPlotRows, delta_t_plot,
                                                dummyInteger, printToFile, readWaveVelFromFile,
                                                generatePlots, ExplicitAcceleration, dummyBoolean,
                                                dummyBoolean2, result_matrix, maxMatrix, minMatrix,
                                                maxAbsMatrix, t_matrix_plot, y_matrix_plot,
                                                z_matrix_plot, v_matrix_plot, a_matrix_plot,
                                                Fsoil_matrix_plot, Fstiff_matrix_plot,
                                                FHrel_matrix_plot, FLrel_matrix_plot,
                                                yref_matrix_plot, iElPl_matrix_plot, outvar_int_matrix)
                except Exception as e:
                    raise RuntimeError(f"Error calling PILSS DLL (Version 1.0). numseeds={numseeds}, Tsimulation={Tsimulation}. Error: {str(e)}") from e
                if self.postproc == 1:
                    return result_matrix, maxMatrix, minMatrix,maxAbsMatrix, t_matrix_plot, y_matrix_plot,z_matrix_plot, v_matrix_plot, a_matrix_plot,Fsoil_matrix_plot, Fstiff_matrix_plot,FHrel_matrix_plot, FLrel_matrix_plot,yref_matrix_plot, iElPl_matrix_plot, outvar_int_matrix
                else:
                    ll =0

            #2.2 PILSS V2 run:
            def run_PILSS_interfacev2(inCross_real, inHydro_real, inHydro_int, seedArray_phase, seedArray_crest,
                                    inSoil_real, inSoil_int, inTime_real, inTime_int,
                                    delta_t, delta_t_signal, delta_t_res, delta_t_plot,
                                    Tsimulation, numseeds, printToFile, readWaveVelFromFile,
                                    generatePlots, ExplicitAcceleration, fileLocation, caseName1, inDyn_real, inDyn_int):

                # Example of input arrays/values/bools which are passed onto Fortran
                # Create mutable string buffers for Fortran to write to
                try:
                    resultsPath = create_fortran_string_buffer(fileLocation)
                except Exception as e:
                    raise ValueError(f"Error creating results path buffer. fileLocation='{fileLocation}': {str(e)}") from e
                
                try:
                    caseName = create_fortran_string_buffer(caseName1)
                except Exception as e:
                    raise ValueError(f"Error creating case name buffer. caseName='{caseName1}': {str(e)}") from e
                
                # Loading the .DLL
                try:
                    if self.bitness == 64:
                        fortlib = ct.CDLL(self.DLL_Location_64bit)
                    else:
                        fortlib = ct.CDLL(self.DLL_Location_32bit)
                except OSError as e:
                    dll_path = self.DLL_Location_64bit if self.bitness == 64 else self.DLL_Location_32bit
                    raise OSError(f"Failed to load {self.bitness}-bit DLL from '{dll_path}'. Error: {str(e)}") from e
                except Exception as e:
                    raise RuntimeError(f"Unexpected error loading DLL (bitness={self.bitness}): {str(e)}") from e

                # Specify input array properties
                fortlib.PILSSInterface_v2.argtypes = [
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # inCross_real
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # inHydro_real
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # inHydro_int
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # seedArray_phase
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # seedArray_crests
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # inSoil_real
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # inSoil_int
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # inTime_real
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # inTime_int
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # NrOfTimesteps
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # NrOfTimesteps_signal
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # NrOfTimesteps_res
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # inDyn_real
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),     # inDyn_int
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='C_CONTIGUOUS'),  # t_vector_U
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # U_t_matrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # A_t_matrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # F_H_matrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # F_L_matrix
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # NrOfPlotsteps
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # addedPlotRows
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=0, flags='C_CONTIGUOUS'),  # delta_t_plot
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # stepLength
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # printToFile
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=0, flags='C_CONTIGUOUS'),  # readWaveVelFromFile
                    np.ctypeslib.ndpointer(dtype=bool, ndim=0, flags='C_CONTIGUOUS'),  # generatePlots
                    np.ctypeslib.ndpointer(dtype=bool, ndim=0, flags='C_CONTIGUOUS'),  # ExplicitAcceleration
                    np.ctypeslib.ndpointer(dtype=bool, ndim=0, flags='C_CONTIGUOUS'),  # dummyBoolean1
                    np.ctypeslib.ndpointer(dtype=bool, ndim=0, flags='C_CONTIGUOUS'),  # dummyBoolean2
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # result_matrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # maxMatrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # minMatrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # maxAbsMatrix
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # t_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # y_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # z_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # v_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # a_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # Fsoil_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # Fstiff_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # FHrel_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # FLrel_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='C_CONTIGUOUS'),  # yref_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='C_CONTIGUOUS'),    # iElPl_matrix_plot
                    np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='C_CONTIGUOUS'),     # outVar_int_matrix
                    ct.POINTER(ct.c_char),  # resultsPath (mutable buffer)
                    ct.POINTER(ct.c_char)   # caseName (mutable buffer)
                    ]

                # Time steps
                NrOfTimesteps = np.require((np.ceil(Tsimulation / delta_t) + 1), dtype=np.int32, requirements=['C'])
                NrOfTimesteps_signal = np.require((np.ceil(Tsimulation / delta_t_signal) + 1), dtype=np.int32, requirements=['C'])
                NrOfTimesteps_res = np.require((np.ceil(Tsimulation / delta_t_res) + 1), dtype=np.int32, requirements=['C'])
                NrOfPlotsteps = np.require((np.ceil(Tsimulation / delta_t_plot) + 1), dtype=np.int32, requirements=['C'])
                t_vector_U = np.require(np.zeros(NrOfTimesteps_signal), dtype=np.float64, requirements=['C'])

                # Results
                U_t_matrix = np.require(np.zeros((numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                A_t_matrix = np.require(np.zeros((numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                F_H_matrix = np.require(np.zeros((numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                F_L_matrix = np.require(np.zeros((numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                result_matrix = np.require(np.zeros((6, 2)), dtype=np.float64, requirements=['C'])
                maxMatrix = np.require(np.zeros((numseeds, 10)), dtype=np.float64, requirements=['C'])
                minMatrix = np.require(np.zeros((numseeds, 10)), dtype=np.float64, requirements=['C'])
                maxAbsMatrix = np.require(np.zeros((numseeds, 10)), dtype=np.float64, requirements=['C'])

                # Plot
                addedPlotRows = 0 if NrOfPlotsteps % 1 == 0 else 1
                if NrOfPlotsteps % 1 == 0:
                    addedPlotRows = np.require(0, dtype=np.int32, requirements=['C'])
                else:
                    addedPlotRows = np.require(1, dtype=np.int32, requirements=['C'])

                t_matrix_plot = np.require(np.zeros((1, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                y_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                z_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                v_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                a_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                Fsoil_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                Fstiff_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                FHrel_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                FLrel_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                yref_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                iElPl_matrix_plot = np.require(np.zeros((numseeds, NrOfPlotsteps), dtype=np.int32), requirements=['C'])
                outvar_int_matrix = np.require(np.zeros((numseeds, 5), dtype=np.int32), requirements=['C'])
                dummyInteger = np.require(1, dtype=np.int32, requirements=['C'])
                dummyBoolean = np.require(False, dtype=bool, requirements=['C'])
                dummyBoolean2 = np.require(True, dtype=bool, requirements=['C'])
                legacyApi = False

                ## Call the Fortran function
                try:
                    fortlib.PILSSInterface_v2(inCross_real, inHydro_real, inHydro_int, seedArray_phase, seedArray_crest,
                                                inSoil_real, inSoil_int, inTime_real, inTime_int,
                                                NrOfTimesteps, NrOfTimesteps_signal, NrOfTimesteps_res,
                                                inDyn_real, inDyn_int, t_vector_U,
                                                U_t_matrix, A_t_matrix, F_H_matrix, F_L_matrix,
                                                NrOfPlotsteps, addedPlotRows, delta_t_plot,
                                                dummyInteger, printToFile, readWaveVelFromFile,
                                                generatePlots, ExplicitAcceleration, dummyBoolean,
                                                dummyBoolean2, result_matrix, maxMatrix, minMatrix,
                                                maxAbsMatrix, t_matrix_plot, y_matrix_plot,
                                                z_matrix_plot, v_matrix_plot, a_matrix_plot,
                                                Fsoil_matrix_plot, Fstiff_matrix_plot,
                                                FHrel_matrix_plot, FLrel_matrix_plot,
                                                yref_matrix_plot, iElPl_matrix_plot, outvar_int_matrix, resultsPath,caseName)
                except Exception as e:
                    raise RuntimeError(f"Error calling PILSS DLL (Version 2.2). Case: {caseName1}, numseeds={numseeds}, Tsimulation={Tsimulation}. Error: {str(e)}") from e
                if self.postproc == 1:
                    return result_matrix, maxMatrix, minMatrix,maxAbsMatrix, t_matrix_plot, y_matrix_plot,z_matrix_plot, v_matrix_plot, a_matrix_plot,Fsoil_matrix_plot, Fstiff_matrix_plot,FHrel_matrix_plot, FLrel_matrix_plot,yref_matrix_plot, iElPl_matrix_plot, outvar_int_matrix
                else:
                    ll =0
            def run():

                try:
                    inCross_real = np.require(np.array([self.D_hydro,self.D, self.w_s,self.w_s_i,self.w_s_w,self.m,0.0,self.t_mgrt,self.k_lay_user,self.EI,self.T0,self.alpha_m]), dtype=np.float64, requirements=['C'])
                except Exception as e:
                    raise ValueError(f"Error creating inCross_real array. Check: D_hydro={self.D_hydro}, D={self.D}, w_s={self.w_s}, m={self.m}. Error: {str(e)}") from e
                
                try:
                    inHydro_real = np.require(np.array([self.rho_w, self.U_m, self.T, self.U_c, self.Phi_t, self.FH_m,0, self.depth, self.Tsim, self.WaveVelRef_h, self.Hs, self.Tp, self.SpectrumPeakedness, self.theta_w, self.n_spreading, self.r_H, self.r_L]), dtype=np.float64, requirements=['C'])
                except Exception as e:
                    raise ValueError(f"Error creating inHydro_real array. Check: Hs={self.Hs}, Tp={self.Tp}, U_c={self.U_c}, depth={self.depth}, Tsim={self.Tsim}. Error: {str(e)}") from e
                
                try:
                    inHydro_int = np.require(np.array([self.HydroModel, self.flowtype, self.roughness, self.GenerateRegularWave, self.SmoothWaveVelocity, self.WaveOrder,self.SpectrumSpecification, self.numseeds, self.HydrodynamicDiameter_int, self.IncludeLiftReduction_int]), dtype=np.int32, requirements=['C'])
                except Exception as e:
                    raise ValueError(f"Error creating inHydro_int array. Check: HydroModel={self.HydroModel}, numseeds={self.numseeds}. Error: {str(e)}") from e
                
                try:
                    seedArray_phase = np.require(self.seedArray_phase, dtype=np.int32, requirements=['C'])
                    seedArray_crest = np.require(self.seedArray_crest, dtype=np.int32, requirements=['C'])
                except Exception as e:
                    raise ValueError(f"Error creating seed arrays. seedArray_phase length={len(self.seedArray_phase)}, seedArray_crest length={len(self.seedArray_crest)}. Error: {str(e)}") from e
                
                try:
                    inSoil_real = np.require(np.array([self.k_soil, self.mu, self.gamma_mark, self.rho_su, self.Nc, self.su_z0, self.delta_mobilization, self.St, self.alpha_soil, self.su_sigmav_NC, self.alpha_brk,self.gamma_pre, self.m_OCR, self.kappa_active, self.kappa_passive, self.su_active, self.su_passive, self.gamma_total, self.su, self.z_ini_user, self.z_t,self.theta_t]), dtype=np.float64, requirements=['C'])
                except Exception as e:
                    raise ValueError(f"Error creating inSoil_real array. Check: k_soil={self.k_soil}, mu={self.mu}, su={self.su}. Error: {str(e)}") from e
                
                try:
                    inSoil_int = np.require(np.array([self.SoilModel, self.CalculatedLayFactor_int, self.UserDefinedLayFactor_int, self.InitialPenetrationModel, self.remoulded_int,self.suction_int, self.waterFilled_int, self.UserDefinedInitialPenetration_int, self.IncludeTrench_int]), dtype=np.int32, requirements=['C'])
                except Exception as e:
                    raise ValueError(f"Error creating inSoil_int array. Check: SoilModel={self.SoilModel}. Error: {str(e)}") from e
                
                try:
                    inTime_real = np.require(np.array([self.t_start, self.delta_t, self.delta_t_signal, self.delta_t_res]), dtype=np.float64, requirements=['C'])
                    inTime_int = np.require(np.array([1]), dtype=np.int32, requirements=['C'])
                    inDyn_real = np.require(np.array([self.RampUpPeriod]), dtype=np.float64, requirements=['C'])
                    inDyn_int = np.require(np.array([self.MaxNrOfIterations, self.RampUp_int]), dtype=np.int32, requirements=['C'])
                    delta_t_plot = np.require(self.delta_t_plot, dtype=np.float64, requirements=['C'])
                except Exception as e:
                    raise ValueError(f"Error creating time/dynamics arrays. Check: delta_t={self.delta_t}, delta_t_signal={self.delta_t_signal}, delta_t_plot={self.delta_t_plot}. Error: {str(e)}") from e
                printToFile = np.require(self.printToFile, dtype=np.int32, requirements=['C'])  # 1 - Print all results to .txt file, 2 - Do not print results to file, 3 - Only print ResultsOverview to file
                generatePlots = np.require(self.generatePlots, dtype=bool, requirements=['C'])
                readWaveVelFromFile = np.require(self.readWaveVelFromFile, dtype=np.int32, requirements=['C'])
                ExplicitAcceleration = np.require(self.ExplicitAcceleration, dtype=bool, requirements=['C'])

                # Validate time step parameters to prevent division by zero
                if self.delta_t_signal <= 0:
                    raise ValueError(f"delta_t_signal must be greater than 0. Current value: {self.delta_t_signal}")
                if self.delta_t_plot <= 0:
                    raise ValueError(f"delta_t_plot must be greater than 0. Current value: {self.delta_t_plot}")
                if self.Tsim <= 0:
                    raise ValueError(f"Tsim (simulation time) must be greater than 0. Current value: {self.Tsim}")

                # Results
                try:
                    NrOfTimesteps_signal = np.require((np.ceil(self.Tsim / self.delta_t_signal) + 1), dtype=np.int32, requirements=['C'])
                except ZeroDivisionError:
                    raise ValueError(f"Division by zero when calculating NrOfTimesteps_signal. Tsim={self.Tsim}, delta_t_signal={self.delta_t_signal}")
                
                U_t_matrix = np.require(np.zeros((self.numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                A_t_matrix = np.require(np.zeros((self.numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                F_H_matrix = np.require(np.zeros((self.numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                F_L_matrix = np.require(np.zeros((self.numseeds, NrOfTimesteps_signal)), dtype=np.float64, requirements=['C'])
                result_matrix = np.require(np.zeros((6, 2)), dtype=np.float64, requirements=['C'])
                maxMatrix = np.require(np.zeros((self.numseeds, 10)), dtype=np.float64, requirements=['C'])
                minMatrix = np.require(np.zeros((self.numseeds, 10)), dtype=np.float64, requirements=['C'])
                maxAbsMatrix = np.require(np.zeros((self.numseeds, 10)), dtype=np.float64, requirements=['C'])
                
                try:
                    NrOfPlotsteps = np.require((np.ceil(self.Tsim / delta_t_plot) + 1), dtype=np.int32, requirements=['C'])
                except ZeroDivisionError:
                    raise ValueError(f"Division by zero when calculating NrOfPlotsteps. Tsim={self.Tsim}, delta_t_plot={delta_t_plot}")

                # Plot
                addedPlotRows = 0 if NrOfPlotsteps % 1 == 0 else 1
                if NrOfPlotsteps % 1 == 0:
                    addedPlotRows = np.require(0, dtype=np.int32, requirements=['C'])
                else:
                    addedPlotRows = np.require(1, dtype=np.int32, requirements=['C'])

                t_matrix_plot = np.require(np.zeros((1, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                y_matrix_plot = np.require(np.zeros((self.numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                z_matrix_plot = np.require(np.zeros((self.numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                v_matrix_plot = np.require(np.zeros((self.numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                a_matrix_plot = np.require(np.zeros((self.numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                Fsoil_matrix_plot = np.require(np.zeros((self.numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                Fstiff_matrix_plot = np.require(np.zeros((self.numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                FHrel_matrix_plot = np.require(np.zeros((self.numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                FLrel_matrix_plot = np.require(np.zeros((self.numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                yref_matrix_plot = np.require(np.zeros((self.numseeds, NrOfPlotsteps)), dtype=np.float64, requirements=['C'])
                iElPl_matrix_plot = np.require(np.zeros((self.numseeds, NrOfPlotsteps), dtype=np.int32), requirements=['C'])
                outvar_int_matrix = np.require(np.zeros((self.numseeds, 5), dtype=np.int32), requirements=['C'])
                dummyInteger = np.require(1, dtype=np.int32, requirements=['C'])
                dummyBoolean = np.require(False, dtype=bool, requirements=['C'])
                dummyBoolean2 = np.require(True, dtype=bool, requirements=['C'])

                #3.2 Running the functions depending on version number:
                if self.Version_number==1:
                    if self.postproc ==1:
                        return result_matrix, maxMatrix, minMatrix,maxAbsMatrix, t_matrix_plot, y_matrix_plot,z_matrix_plot, v_matrix_plot, a_matrix_plot,Fsoil_matrix_plot, Fstiff_matrix_plot,FHrel_matrix_plot, FLrel_matrix_plot,yref_matrix_plot, iElPl_matrix_plot, outvar_int_matrix
                    else:
                        # pass instance attributes where needed to avoid undefined names
                        try:
                            run_PILSS_interfacev1(
                                inCross_real, inHydro_real, inHydro_int,
                                seedArray_phase, seedArray_crest,
                                inSoil_real, inSoil_int, inTime_real, inTime_int,
                                self.delta_t, self.delta_t_signal, self.delta_t_res, delta_t_plot,
                                self.Tsim, self.numseeds, printToFile, readWaveVelFromFile,
                                generatePlots, ExplicitAcceleration
                            )
                        except Exception as e:
                            raise RuntimeError(f"PILSS v1.0 execution failed. Case: {self.caseName}, Tsim={self.Tsim}, numseeds={self.numseeds}. Error: {str(e)}") from e
                elif self.Version_number==2:
                    if self.postproc==1:
                        return result_matrix, maxMatrix, minMatrix,maxAbsMatrix, t_matrix_plot, y_matrix_plot,z_matrix_plot, v_matrix_plot, a_matrix_plot,Fsoil_matrix_plot, Fstiff_matrix_plot,FHrel_matrix_plot, FLrel_matrix_plot,yref_matrix_plot, iElPl_matrix_plot, outvar_int_matrix
                    else:
                        # pass instance attributes and local inDyn arrays
                        try:
                            run_PILSS_interfacev2(
                                inCross_real, inHydro_real, inHydro_int,
                                seedArray_phase, seedArray_crest,
                                inSoil_real, inSoil_int, inTime_real, inTime_int,
                                self.delta_t, self.delta_t_signal, self.delta_t_res, delta_t_plot,
                                self.Tsim, self.numseeds, printToFile, readWaveVelFromFile,
                                generatePlots, ExplicitAcceleration, self.fileLocation, self.caseName,
                                inDyn_real, inDyn_int
                            )
                        except Exception as e:
                            raise RuntimeError(f"PILSS v2.2 execution failed. Case: {self.caseName}, Tsim={self.Tsim}, numseeds={self.numseeds}. Error: {str(e)}") from e
                else:
                    print("Please specify version number")
                
                # Return summary of execution
                return {
                    "status": "completed",
                    "case_name": self.caseName,
                    "version": f"{self.Version_number}.{'0' if self.Version_number == 1 else '2'}",
                    "results_location": self.fileLocation,
                    "simulation_time": self.Tsim,
                    "num_seeds": self.numseeds
                }

                #4.0 Optional postprocessing of the Results data:
                print(t_matrix_plot)


                import matplotlib.pyplot as plt
                if self.postproc==1:
                    #4.1 Example of postprocessing of results:
                    time = t_matrix_plot[0,:]
                    plt.figure()
                    plt.plot(t_matrix_plot, y_matrix_plot[0,:], label='y')
                    plt.xlabel('Time (s)')
                    plt.ylabel('Displacement (m)')
                    plt.title('Displacement time series for element 1')
                    plt.legend()
                    plt.grid()
                    plt.show()
            run()

class PILSSResults(BaseResults):
    """
    Results class to grab the values from the PILSS simulation.
    """

    def __init__(self, resultsFolder: str):
        super().__init__(resultsFolder)
        self.sum: Optional[float] = None
        self.pilss_files: Optional[Dict[str, str]] = None
        self.displacement_data: Optional[Dict[str, Any]] = None

    def wait_for_results_file(self, case_name: str, timeout: int = 60) -> Optional[str]:
        """
        Waits for the {Casename}_ResultsOverview.txt file to be generated in the specified location.

        :param case_name: The base name of the case (e.g., "ExampleCase").
        :param timeout: Maximum time to wait for the file in seconds.
        :return: The full path to the file if found, None otherwise.
        """
        import time
        results_file = os.path.join(self.resultsFolder, f"{case_name}_ResultsOverview.txt")
        start_time = time.time()

        while time.time() - start_time < timeout:
            if os.path.exists(results_file):
                return results_file
            time.sleep(1)  # Wait for 1 second before checking again

        print(f"File {results_file} not found within {timeout} seconds.")
        return None

    def extract_displacement_data(self, file_path: str) -> Dict[str, Any]:
        """
        Extracts displacement data from the ResultsOverview.txt file.

        :param file_path: Path to the ResultsOverview.txt file.
        :return: A dictionary with the extracted displacement data.
        """
        displacement_data = {
            "Total design (avg + 1 std)": None,
            "Average (max.abs.)": None,
            "Standard dev. (max.abs.)": None,
        }

        with open(file_path, 'r') as file:
            pre_line = ""
            for line in file:
                if "DESIGN DISPLACEMENT (1 avg. + 1 std.dev.) [m]:" in pre_line:
                    displacement_data["Total design (avg + 1 std)"] = line.strip()
                elif "Average absolute max.:" in pre_line:
                    cleanLine = ",".join(line.split())
                    displacement_data["Average (max.abs.)"] = cleanLine.split(",")[2].strip()
                elif "Std. dev. abs. max.:" in pre_line:
                    cleanLine = ",".join(line.split())
                    displacement_data["Standard dev. (max.abs.)"] = cleanLine.split(",")[2].strip()
                pre_line = line

        return displacement_data

    def process_results(self) -> Dict[str, Any]:
        print("ResultsFolder =" + self.resultsFolder)
        
        # Grab all PILSS output files from the results folder
        self.pilss_files = {}
        results_overview_file = None
        
        if os.path.exists(self.resultsFolder):
            for filename in os.listdir(self.resultsFolder):
                file_path = os.path.join(self.resultsFolder, filename)
                # Only include actual files (not directories) and skip the results.json
                if os.path.isfile(file_path) and filename != 'results.json':
                    self.pilss_files[filename] = file_path
                    # Check if this is a ResultsOverview file
                    if filename.endswith('_ResultsOverview.txt'):
                        results_overview_file = file_path
        
        # Extract displacement data if we found a ResultsOverview file
        if results_overview_file and os.path.exists(results_overview_file):
            try:
                self.displacement_data = self.extract_displacement_data(results_overview_file)
            except Exception as e:
                print(f"Error extracting displacement data: {e}")
                self.displacement_data = {"error": str(e)}
        
        # Get any additional data from results.json if it exists
        data = self.getData()
        self.sum = data.get("sum")
        
        result = {
            "sum": self.sum,
            "pilss_output_files": self.pilss_files,
            "file_count": len(self.pilss_files)
        }
        
        # Add displacement data if available
        if self.displacement_data:
            result["displacement_data"] = self.displacement_data
        
        return result
try:
    from .adapters import DownloadableClass
except ImportError:
    from adapters import DownloadableClass

try:
    from .Templates import define_template
except ImportError:
    from Templates import define_template


class PILSSDownloadable(DownloadableClass):
    def generateDownloadable(self, case_number, file_format='json'):
        case = self.get_case_by_number(case_number)

        if file_format == 'json':
            import json
            return {
                'filename': f'pilss_case_{case_number}.json',
                'data': json.dumps(case.case_data, indent=2),
                'mimetype': 'application/json',
            }

        if file_format == 'csv':
            import csv
            import io

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['parameter', 'value', 'units'])
            writer.writeheader()

            for key, value_dict in case.case_data.items():
                if isinstance(value_dict, dict):
                    value = value_dict.get('value', '')
                    units = value_dict.get('units', '')
                else:
                    value = value_dict
                    units = ''
                writer.writerow({'parameter': key, 'value': value, 'units': units})

            return {
                'filename': f'pilss_case_{case_number}.csv',
                'data': output.getvalue(),
                'mimetype': 'text/csv',
            }

        raise ValueError(f"Unsupported format: {file_format}")

    def generateDownloadableMultiple(self, case_numbers=None, file_format='json'):
        cases_to_download = self.cases if case_numbers is None else [
            self.get_case_by_number(num) for num in case_numbers
        ]

        if file_format == 'json':
            import json
            payload = {
                'job_uuid': self.job_uuid,
                'cases': [case.case_data for case in cases_to_download],
            }
            return {
                'filename': f'pilss_job_{self.job_uuid}_cases.json',
                'data': json.dumps(payload, indent=2),
                'mimetype': 'application/json',
            }

        if file_format == 'csv':
            import csv
            import io

            all_params = set()
            for case in cases_to_download:
                all_params.update(case.case_data.keys())
            all_params = sorted(all_params)

            output = io.StringIO()
            fieldnames = ['case_number'] + all_params
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for case in cases_to_download:
                row = {'case_number': case.caseNumber}
                for param in all_params:
                    value_obj = case.case_data.get(param, '')
                    if isinstance(value_obj, dict):
                        value = value_obj.get('value', '')
                        units = value_obj.get('units', '')
                        row[param] = f"{value} {units}".strip()
                    else:
                        row[param] = value_obj
                writer.writerow(row)

            return {
                'filename': f'pilss_job_{self.job_uuid}_cases.csv',
                'data': output.getvalue(),
                'mimetype': 'text/csv',
            }

        raise ValueError(f"Unsupported format: {file_format}")


class PILSSSchemaTemplate:
    def __init__(self):
        schema = object.__new__(PILSSAction).mySchema()
        properties = schema.get('properties', {}) if isinstance(schema, dict) else {}
        children = []
        for name, definition in properties.items():
            children.append({
                'type': 'parameter',
                'name': name,
                'parameter_type': definition.get('type', 'string'),
                'description': definition.get('description', definition.get('title', '')),
                'units': definition.get('x-units', definition.get('units', '')),
            })

        self.name = 'PILSS Input Template'
        self.description = 'Template generated from PILSS action schema'
        self.template = define_template(
            name=self.name,
            description=self.description,
            node_definitions=[{'type': 'group', 'name': 'PILSS', 'children': children}],
        )

    def to_frontend_parameters(self):
        return self.template.to_frontend_parameters()

    def toFrontend_parameters(self):
        return self.to_frontend_parameters()


class PILSSOnBottomTemplate:
    def __init__(self):
        update_keys = [
            'Version_number', 'bitness', 'U_c', 'depth', 'Tsim', 'Hs', 'Tp',
            'theta_w', 'roughness', 'seedArray_phase', 'seedArray_crest',
            'k_soil', 'gamma_mark', 'rho_su', 'su_z0', 'delta_mobilization',
            'alpha_soil', 'gamma_total', 'SoilModel', 'InitialPenetrationModel',
            'delta_t', 'delta_t_res', 'delta_t_plot', 'RampUpPeriod', 'RampUp_int',
        ]

        integer_params = {
            'Version_number', 'bitness', 'Tsim', 'roughness', 'SoilModel',
            'InitialPenetrationModel', 'RampUp_int'
        }
        list_params = {'seedArray_phase', 'seedArray_crest'}

        children = []
        for key in update_keys:
            if key in list_params:
                param_type = 'array'
            elif key in integer_params:
                param_type = 'integer'
            else:
                param_type = 'number'

            children.append({
                'type': 'parameter',
                'name': key,
                'parameter_type': param_type,
                'description': 'Defined by update_job defaults',
                'units': '',
            })

        self.name = 'PILSS OnBottom Template'
        self.description = 'Template for PILSS OnBottom job profile'
        self.template = define_template(
            name=self.name,
            description=self.description,
            node_definitions=[{'type': 'group', 'name': 'PILSS', 'children': children}],
        )

    def to_frontend_parameters(self):
        return self.template.to_frontend_parameters()

    def toFrontend_parameters(self):
        return self.to_frontend_parameters()


PILSSUpdateTemplate = PILSSOnBottomTemplate
PILSSTemplate = PILSSOnBottomTemplate

# Backward-compatible aliases for code paths still using the Add* naming convention.
AddAction = PILSSAction
AddResults = PILSSResults
AddTemplate = PILSSOnBottomTemplate
AddDownloadable = PILSSDownloadable
