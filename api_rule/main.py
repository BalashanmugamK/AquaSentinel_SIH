import pyngrok.ngrok
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uvicorn

app = FastAPI(
    title="Water Quality Inspection API",
    description="Rule-based real-time water quality inspection using sensor data",
    version="1.0.0"
)

class WaterQualityInput(BaseModel):

    temperature: float = Field(..., description="Temperature in degree Celsius")
    ph: float = Field(..., ge=0, le=14, description="pH value")

    turbidity: float = Field(
        ...,
        ge=0,
        description="Turbidity in NTU"
    )

    tds: float = Field(
        ...,
        ge=0,
        description="Total Dissolved Solids in mg/L"
    )

    electrical_conductivity: float = Field(
        ...,
        ge=0,
        description="Electrical Conductivity in µS/cm"
    )

    orp: float = Field(
        ...,
        description="Oxidation Reduction Potential in mV"
    )

    dissolved_oxygen: float = Field(
        ...,
        ge=0,
        description="Dissolved Oxygen in mg/L"
    )

    salinity: float = Field(
        ...,
        ge=0,
        description="Salinity in ppt"
    )

    nitrate: float = Field(
        ...,
        ge=0,
        description="Nitrate NO3- concentration in mg/L"
    )

    ammonia: float = Field(
        ...,
        ge=0,
        description="Ammonia concentration in mg/L"
    )


def classify_tds(value: float) -> str:

    if value < 300:
        return "Low"
    elif value <= 500:
        return "Medium"
    elif value <= 1000:
        return "High"
    else:
        return "Extreme"


def classify_temperature(value: float) -> str:

    if value < 15:
        return "Low"
    elif value <= 30:
        return "Normal"
    else:
        return "High"


def classify_ph(value: float) -> str:

    if value < 4.5:
        return "Highly Acidic"
    elif value < 6.5:
        return "Slightly Acidic"
    elif value <= 7.5:
        return "Neutral"
    elif value <= 8.5:
        return "Slightly Basic"
    else:
        return "Highly Basic"


def classify_turbidity(value: float) -> str:

    if value < 1:
        return "Low"
    elif value <= 5:
        return "Medium"
    elif value <= 10:
        return "High"
    else:
        return "Extreme"


def classify_ec(value: float) -> str:

    if value < 500:
        return "Low"
    elif value <= 1500:
        return "Medium"
    elif value <= 2500:
        return "High"
    else:
        return "Extreme"


def classify_orp(value: float) -> str:

    if value < 100:
        return "Strongly Reducing / High Contamination Risk"
    elif value < 300:
        return "Reducing / Contamination Risk"
    elif value <= 500:
        return "Natural Oxidizing"
    else:
        return "Strongly Oxidizing / Treated"


def classify_dissolved_oxygen(value: float) -> str:

    if value < 4:
        return "Low"
    elif value <= 7:
        return "Medium"
    else:
        return "High"


def classify_salinity(value: float) -> str:

    if value < 0.5:
        return "Freshwater / Low"
    elif value <= 5:
        return "Slightly Saline / Medium"
    else:
        return "Saline / High"


def classify_nitrate(value: float) -> str:

    if value < 25:
        return "Low"
    elif value <= 50:
        return "Medium"
    else:
        return "High"


def classify_ammonia(value: float) -> str:

    if value < 0.5:
        return "Low"
    elif value <= 1.5:
        return "Medium"
    else:
        return "High"


# ============================================================
# WASTEWATER / SEWAGE DETECTION
# ============================================================

def detect_sewage_intrusion(data: WaterQualityInput) -> Dict[str, Any]:

    score = 0
    reasons = []

    # High ammonia
    if data.ammonia > 1.5:
        score += 2
        reasons.append("Elevated ammonia")

    # High nitrate
    if data.nitrate > 50:
        score += 2
        reasons.append("Elevated nitrate")

    # High turbidity
    if data.turbidity > 5:
        score += 2
        reasons.append("High turbidity")

    # High EC
    if data.electrical_conductivity > 1500:
        score += 1
        reasons.append("High electrical conductivity")

    # High TDS
    if data.tds > 1000:
        score += 1
        reasons.append("High TDS")

    # Low dissolved oxygen
    if data.dissolved_oxygen < 4:
        score += 2
        reasons.append("Low dissolved oxygen")

    # Low ORP
    if data.orp < 200:
        score += 2
        reasons.append("Low ORP / reducing conditions")

    # Abnormal pH
    if data.ph < 6.5 or data.ph > 8.5:
        score += 1
        reasons.append("pH outside normal drinking-water range")

    detected = "Yes" if score >= 5 else "No"

    if score >= 8:
        risk = "High"
    elif score >= 5:
        risk = "Moderate"
    else:
        risk = "Low"

    return {
        "detected": detected,
        "risk": risk,
        "score": score,
        "reasons": reasons
    }



def detect_organic_decay(data: WaterQualityInput) -> Dict[str, Any]:

    score = 0
    reasons = []

    # Low dissolved oxygen
    if data.dissolved_oxygen < 4:
        score += 2
        reasons.append("Low dissolved oxygen")

    # Reducing conditions
    if data.orp < 200:
        score += 2
        reasons.append("Low ORP / reducing conditions")

    # Elevated ammonia
    if data.ammonia > 1.5:
        score += 2
        reasons.append("Elevated ammonia")

    # High turbidity
    if data.turbidity > 5:
        score += 1
        reasons.append("High turbidity")

    # Elevated nitrate
    if data.nitrate > 25:
        score += 1
        reasons.append("Elevated nitrate")

    # High TDS
    if data.tds > 1000:
        score += 1
        reasons.append("High TDS")

    # High conductivity
    if data.electrical_conductivity > 1500:
        score += 1
        reasons.append("High electrical conductivity")

    detected = "Yes" if score >= 5 else "No"

    if score >= 7:
        risk = "High"
    elif score >= 5:
        risk = "Moderate"
    else:
        risk = "Low"

    return {
        "detected": detected,
        "risk": risk,
        "score": score,
        "reasons": reasons
    }


@app.post("/inspect")
def inspect_water(data: WaterQualityInput):


    results = {

        "tds": {
            "value": data.tds,
            "unit": "mg/L",
            "classification": classify_tds(data.tds)
        },

        "temperature": {
            "value": data.temperature,
            "unit": "°C",
            "classification": classify_temperature(data.temperature)
        },

        "ph": {
            "value": data.ph,
            "classification": classify_ph(data.ph)
        },

        "turbidity": {
            "value": data.turbidity,
            "unit": "NTU",
            "classification": classify_turbidity(data.turbidity)
        },

        "electrical_conductivity": {
            "value": data.electrical_conductivity,
            "unit": "µS/cm",
            "classification": classify_ec(
                data.electrical_conductivity
            )
        },

        "orp": {
            "value": data.orp,
            "unit": "mV",
            "classification": classify_orp(data.orp)
        },

        "dissolved_oxygen": {
            "value": data.dissolved_oxygen,
            "unit": "mg/L",
            "classification": classify_dissolved_oxygen(
                data.dissolved_oxygen
            )
        },

        "salinity": {
            "value": data.salinity,
            "unit": "ppt",
            "classification": classify_salinity(data.salinity)
        },

        "nitrate": {
            "value": data.nitrate,
            "unit": "mg/L",
            "classification": classify_nitrate(data.nitrate)
        },

        "ammonia": {
            "value": data.ammonia,
            "unit": "mg/L",
            "classification": classify_ammonia(data.ammonia)
        }
    }


    sewage_result = detect_sewage_intrusion(data)

    organic_result = detect_organic_decay(data)


    return {

        "status": "success",

        "input": data.model_dump(),

        "single_parameter_analysis": results,

        "multi_parameter_analysis": {

            "wastewater_or_sewage_intrusion": sewage_result,

            "organic_matter_or_animal_decay": organic_result
        }
    }


@app.get("/")
def home():

    return {
        "message": "Water Quality Inspection API is running"
    }

if __name__ == "__main__":
    url = pyngrok.ngrok.connect(8000)
    print(url)
    uvicorn.run(app, host="localhost", port=8000)
