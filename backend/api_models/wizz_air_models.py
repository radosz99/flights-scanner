#!/usr/bin/env python3

"""
Pydantic models for Wizz Air API responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta


class Price(BaseModel):
    """Price model used throughout the API."""
    amount: float
    currencyCode: str
    exchangedAmount: Optional[float] = None
    exchangedCurrencyCode: Optional[str] = None


class WDC(BaseModel):
    """Wizz Discount Club information."""
    type: str
    countryCode: Optional[str] = None
    isInternational: bool
    isDomestic: bool


class Fee(BaseModel):
    """Fee information."""
    included: bool
    specificType: str
    displayCount: int
    discountPrice: Optional[Price] = None
    price: Price
    promotedPrice: Optional[Price] = None
    order: int
    code: str
    coupon: Optional[str] = None


class FlightPriceDetail(BaseModel):
    """Detailed price breakdown for a flight."""
    discountedBundlePrice: Price
    originalBundlePrice: Price
    bundleDiscountPrice: Price
    baseFarePrice: float
    discountRate: float
    discountPrice: Price
    price: Price
    fees: List[Fee]
    displayCount: int
    promotedPrice: Optional[Price] = None
    promotionValue: float
    isFareCouponUsed: bool
    total: Price


class Promotion(BaseModel):
    """Promotion information."""
    # Add fields as needed based on actual API responses
    pass


class Fare(BaseModel):
    """Fare information for different bundle types."""
    fareSellKey: str
    administrationFeePrice: Price
    fullBasePrice: Price
    basePrice: Price
    discountedPriceWithoutFamilyDiscount: Price
    discountedPrice: Price
    discountPrice: Price
    pastPrice: Optional[Price] = None
    discountedBundlePrice: Price
    originalBundlePrice: Price
    bundleDiscountPrice: Price
    baseFarePrice: float
    discountedFarePrice: float
    baseFarePriceWithAdministrationFee: Price
    discountedFarePriceWithAdministrationFee: Price
    flightChangeFeePrice: Price
    fareLockPrice: Price
    flightPriceDetail: FlightPriceDetail
    passengerFlightPriceDetails: Optional[dict] = None
    bundle: str  # "basic", "smart", "middleTwo", "plus"
    fareDiscountType: str
    wdc: Optional[WDC] = None
    distributionFeePrice: Price
    isFamily: bool
    soldOut: bool
    groupAdministrationFeePrice: Price
    promotion: Optional[Promotion] = None


class LimitExceeded(BaseModel):
    """Limit exceeded information."""
    limitExceeded: bool
    isBlocking: bool
    unavailableCount: Optional[int] = None


class Flight(BaseModel):
    """Flight information with fares and details."""
    departureStation: str
    arrivalStation: str
    aircraftName: str
    carrierCode: str
    operatingCarrierCode: Optional[str] = None
    flightNumber: str
    opSuffix: str
    flightSellKey: str
    departureDateTime: str
    departureTimeUtcOffset: str
    arrivalDateTime: str
    arrivalTimeUtcOffset: str
    fares: List[Fare]
    infantLimitExceeded: LimitExceeded
    wheelchairLimitExceeded: LimitExceeded
    oxyLimitExceeded: LimitExceeded
    sportsEquipmentLimitExceeded: LimitExceeded
    autoCheckInLimitExceeded: LimitExceeded
    isRequest: bool
    isLease: bool
    duration: str

    @property
    def departure_time(self) -> datetime:
        """Parse departure datetime."""
        return datetime.fromisoformat(self.departureDateTime)

    @property
    def arrival_time(self) -> datetime:
        """Parse arrival datetime."""
        return datetime.fromisoformat(self.arrivalDateTime)

    @property
    def flight_duration_minutes(self) -> int:
        """Get flight duration in minutes."""
        h, m, s = self.duration.split(":")
        return int(h) * 60 + int(m)

    def get_cheapest_fare(self) -> Optional[Fare]:
        """Get the cheapest available fare."""
        available_fares = [f for f in self.fares if not f.soldOut]
        if not available_fares:
            return None
        return min(available_fares, key=lambda f: f.basePrice.amount)


class AncillaryService(BaseModel):
    """Ancillary service information."""
    name: Optional[str] = None
    key: str


class BundleCardTopBlock(BaseModel):
    """Bundle card top block information."""
    showTicketPrice: bool
    ancillaryServices: List[str]


class Bundle(BaseModel):
    """Bundle information (basic, smart, middleTwo, plus)."""
    code: str
    ancillaryServices: List[str]
    fareLockFeeCode: str
    groupedAncillaryServices: List[AncillaryService]
    bundleCardTopBlock: BundleCardTopBlock


class FlightDatesResponse(BaseModel):
    """Response from the flight dates API."""
    flightDates: List[str]

    def get_dates_as_datetime(self) -> List[datetime]:
        """Convert flight dates to datetime objects."""
        return [datetime.fromisoformat(date) for date in self.flightDates]


class SearchResponse(BaseModel):
    """Main search response from Wizz Air API."""
    outboundFlights: List[Flight]
    returnFlights: List[Flight]
    outboundBundles: List[Bundle]
    returnBundles: List[Bundle]
    outboundCo2Emission: Optional[dict] = None
    returnCo2Emission: Optional[dict] = None
    currencyCode: str
    arrivalStationCurrencyCode: str
    isDomestic: bool
    isGroup: bool
    discountType: str
    discountPercentage: float
    bookingCurrencyRenewalPrice: Optional[Price] = None
    connectedFlight: Optional[dict] = None
    isBundleCompositionWarningTextVisible: bool
    isWdcPremiumEnabled: bool
    isPrivilegePassAllowed: bool
    isSmartBundleWarningTextVisible: bool
    isMetaSearchSourceDisableBundleAB: bool
    isOutboundAirportCheckinFree: bool
    isReturnAirportCheckinFree: bool
    var99: bool

    def get_all_flights(self) -> List[Flight]:
        """Get all flights (outbound + return)."""
        return self.outboundFlights + self.returnFlights

    def get_cheapest_outbound(self) -> Optional[Flight]:
        """Get the cheapest outbound flight."""
        if not self.outboundFlights:
            return None
        return min(
            self.outboundFlights,
            key=lambda f: f.get_cheapest_fare().basePrice.amount if f.get_cheapest_fare() else float('inf')
        )

    def get_cheapest_return(self) -> Optional[Flight]:
        """Get the cheapest return flight."""
        if not self.returnFlights:
            return None
        return min(
            self.returnFlights,
            key=lambda f: f.get_cheapest_fare().basePrice.amount if f.get_cheapest_fare() else float('inf')
        )

    def get_total_cheapest_price(self) -> Optional[float]:
        """Get the total cheapest price for round trip."""
        outbound = self.get_cheapest_outbound()
        return_flight = self.get_cheapest_return()

        if not outbound or not return_flight:
            return None

        outbound_fare = outbound.get_cheapest_fare()
        return_fare = return_flight.get_cheapest_fare()

        if not outbound_fare or not return_fare:
            return None

        return outbound_fare.basePrice.amount + return_fare.basePrice.amount
