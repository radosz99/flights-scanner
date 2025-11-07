from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Fare(BaseModel):
    type: str
    amount: float
    count: int
    hasDiscount: bool
    publishedFare: float
    discountInPercent: int
    hasPromoDiscount: bool
    discountAmount: float
    hasBogof: bool
    isPrime: bool


class RegularFare(BaseModel):
    fareKey: str
    fares: List[Fare]


class Segment(BaseModel):
    segmentNr: int
    origin: str
    destination: str
    flightNumber: str
    time: List[str]
    timeUTC: List[str]
    duration: str


class Flight(BaseModel):
    faresLeft: int
    flightKey: str
    infantsLeft: int
    regularFare: Optional[RegularFare] = None
    operatedBy: str
    segments: List[Segment]
    isSSIMLoad: bool
    flightNumber: str
    time: List[str]
    timeUTC: List[str]
    duration: str


class FlightDate(BaseModel):
    dateOut: str
    flights: List[Flight]


class Trip(BaseModel):
    origin: str
    originName: str
    destination: str
    destinationName: str
    isSpanishDomestic: bool
    minDepartureTime: int
    minConnectionTime: int
    routeGroup: str
    tripType: str
    upgradeType: str
    dates: List[FlightDate]


class RyanairResponse(BaseModel):
    termsOfUse: str
    currency: str
    currPrecision: int
    routeGroup: str
    tripType: str
    upgradeType: str
    trips: List[Trip]
    serverTimeUTC: str
