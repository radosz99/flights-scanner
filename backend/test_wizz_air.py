#!/usr/bin/env python3

"""
Test script for Wizz Air models with sample data.

Note: The actual Wizz Air API blocks automated requests (403 Forbidden).
This test demonstrates the parsing logic works correctly with sample data.
"""

from api_models.wizz_air_models import (
    FlightDatesResponse,
    SearchResponse,
    Flight,
    Fare,
    Price,
)
import json


def test_flight_dates_parsing():
    """Test parsing of flight dates response."""
    print("Testing Flight Dates Response Parsing")
    print("=" * 60)

    sample_data = {
        "flightDates": [
            "2025-12-13T00:00:00",
            "2025-12-16T00:00:00",
            "2025-12-18T00:00:00",
            "2025-12-20T00:00:00",
            "2025-12-23T00:00:00",
        ]
    }

    response = FlightDatesResponse(**sample_data)
    print(f"✓ Parsed {len(response.flightDates)} flight dates")

    dates_as_dt = response.get_dates_as_datetime()
    print(f"✓ Converted to datetime objects: {dates_as_dt[0].strftime('%Y-%m-%d')}")

    return response


def test_search_response_parsing():
    """Test parsing of search response with sample flight data."""
    print("\n\nTesting Search Response Parsing")
    print("=" * 60)

    # Minimal sample data structure
    sample_flight = {
        "departureStation": "WRO",
        "arrivalStation": "NCE",
        "aircraftName": "Airbus A321neo",
        "carrierCode": "W6",
        "operatingCarrierCode": None,
        "flightNumber": "1829",
        "opSuffix": " ",
        "flightSellKey": "W6~1829~ ~~WRO~12/13/2025 18:35~NCE~12/13/2025 20:35~~",
        "departureDateTime": "2025-12-13T18:35:00",
        "departureTimeUtcOffset": "01:00:00",
        "arrivalDateTime": "2025-12-13T20:35:00",
        "arrivalTimeUtcOffset": "01:00:00",
        "fares": [
            {
                "fareSellKey": "test_key",
                "administrationFeePrice": {"amount": 38.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "fullBasePrice": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "basePrice": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountedPriceWithoutFamilyDiscount": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountedPrice": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "pastPrice": {"amount": 99.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountedBundlePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "originalBundlePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "bundleDiscountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "baseFarePrice": 52.0,
                "discountedFarePrice": 52.0,
                "baseFarePriceWithAdministrationFee": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountedFarePriceWithAdministrationFee": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "flightChangeFeePrice": {"code": None, "amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "fareLockPrice": {"amount": 13.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "flightPriceDetail": {
                    "discountedBundlePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "originalBundlePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "bundleDiscountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "baseFarePrice": 52.0,
                    "discountRate": 0.0,
                    "discountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "price": {"amount": 52.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "fees": [
                        {
                            "included": False,
                            "specificType": "administration",
                            "displayCount": 1,
                            "discountPrice": None,
                            "price": {"amount": 38.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                            "promotedPrice": None,
                            "order": 0,
                            "code": "ADM",
                            "coupon": None
                        }
                    ],
                    "displayCount": 1,
                    "promotedPrice": None,
                    "promotionValue": 0.0,
                    "isFareCouponUsed": False,
                    "total": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None}
                },
                "passengerFlightPriceDetails": None,
                "bundle": "basic",
                "fareDiscountType": "none",
                "wdc": {"type": "international", "countryCode": None, "isInternational": True, "isDomestic": False},
                "distributionFeePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "isFamily": False,
                "soldOut": False,
                "groupAdministrationFeePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "promotion": None
            },
            {
                "fareSellKey": "test_key_2",
                "administrationFeePrice": {"amount": 38.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "fullBasePrice": {"amount": 288.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "basePrice": {"amount": 219.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountedPriceWithoutFamilyDiscount": {"amount": 219.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountedPrice": {"amount": 219.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "pastPrice": None,
                "discountedBundlePrice": {"amount": 129.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "originalBundlePrice": {"amount": 129.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "bundleDiscountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "baseFarePrice": 52.0,
                "discountedFarePrice": 52.0,
                "baseFarePriceWithAdministrationFee": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountedFarePriceWithAdministrationFee": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "flightChangeFeePrice": {"code": None, "amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "fareLockPrice": {"amount": 13.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "flightPriceDetail": {
                    "discountedBundlePrice": {"amount": 129.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "originalBundlePrice": {"amount": 129.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "bundleDiscountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "baseFarePrice": 52.0,
                    "discountRate": 0.0,
                    "discountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "price": {"amount": 181.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "fees": [
                        {
                            "included": False,
                            "specificType": "administration",
                            "displayCount": 1,
                            "discountPrice": None,
                            "price": {"amount": 38.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                            "promotedPrice": None,
                            "order": 0,
                            "code": "ADM",
                            "coupon": None
                        }
                    ],
                    "displayCount": 1,
                    "promotedPrice": None,
                    "promotionValue": 0.0,
                    "isFareCouponUsed": False,
                    "total": {"amount": 219.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None}
                },
                "passengerFlightPriceDetails": None,
                "bundle": "smart",
                "fareDiscountType": "none",
                "wdc": {"type": "international", "countryCode": None, "isInternational": True, "isDomestic": False},
                "distributionFeePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "isFamily": False,
                "soldOut": False,
                "groupAdministrationFeePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "promotion": None
            }
        ],
        "infantLimitExceeded": {"limitExceeded": False, "isBlocking": True},
        "wheelchairLimitExceeded": {"unavailableCount": 0, "limitExceeded": False, "isBlocking": False},
        "oxyLimitExceeded": {"limitExceeded": False, "isBlocking": True},
        "sportsEquipmentLimitExceeded": {"unavailableCount": 0, "limitExceeded": False, "isBlocking": False},
        "autoCheckInLimitExceeded": {"unavailableCount": 0, "limitExceeded": False, "isBlocking": False},
        "isRequest": False,
        "isLease": False,
        "duration": "02:00:00"
    }

    # Parse a single flight
    flight = Flight(**sample_flight)
    print(f"\n✓ Parsed flight: {flight.flightNumber}")
    print(f"  Route: {flight.departureStation} -> {flight.arrivalStation}")
    print(f"  Departure: {flight.departureDateTime}")
    print(f"  Arrival: {flight.arrivalDateTime}")
    print(f"  Duration: {flight.duration} ({flight.flight_duration_minutes} minutes)")
    print(f"  Aircraft: {flight.aircraftName}")
    print(f"  Number of fare options: {len(flight.fares)}")

    # Test cheapest fare finding
    cheapest = flight.get_cheapest_fare()
    if cheapest:
        print(f"\n✓ Cheapest fare:")
        print(f"  Bundle: {cheapest.bundle}")
        print(f"  Price: {cheapest.basePrice.amount} {cheapest.basePrice.currencyCode}")
        print(f"  Administration fee: {cheapest.administrationFeePrice.amount} {cheapest.administrationFeePrice.currencyCode}")

    # Test all bundle types
    print(f"\n✓ Available bundles:")
    for fare in flight.fares:
        print(f"  - {fare.bundle}: {fare.basePrice.amount} {fare.basePrice.currencyCode}")

    return flight


def test_full_search_response():
    """Test parsing a minimal full search response."""
    print("\n\nTesting Full Search Response")
    print("=" * 60)

    # Create a minimal search response with the flight from above
    sample_flight_data = {
        "departureStation": "WRO",
        "arrivalStation": "NCE",
        "aircraftName": "Airbus A321neo",
        "carrierCode": "W6",
        "operatingCarrierCode": None,
        "flightNumber": "1829",
        "opSuffix": " ",
        "flightSellKey": "W6~1829~ ~~WRO~12/13/2025 18:35~NCE~12/13/2025 20:35~~",
        "departureDateTime": "2025-12-13T18:35:00",
        "departureTimeUtcOffset": "01:00:00",
        "arrivalDateTime": "2025-12-13T20:35:00",
        "arrivalTimeUtcOffset": "01:00:00",
        "fares": [
            {
                "fareSellKey": "test", "administrationFeePrice": {"amount": 38.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "fullBasePrice": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "basePrice": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountedPriceWithoutFamilyDiscount": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountedPrice": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "pastPrice": None, "discountedBundlePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "originalBundlePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "bundleDiscountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "baseFarePrice": 52.0, "discountedFarePrice": 52.0,
                "baseFarePriceWithAdministrationFee": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "discountedFarePriceWithAdministrationFee": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "flightChangeFeePrice": {"code": None, "amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "fareLockPrice": {"amount": 13.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "flightPriceDetail": {
                    "discountedBundlePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "originalBundlePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "bundleDiscountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "baseFarePrice": 52.0, "discountRate": 0.0,
                    "discountPrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "price": {"amount": 52.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                    "fees": [], "displayCount": 1, "promotedPrice": None, "promotionValue": 0.0, "isFareCouponUsed": False,
                    "total": {"amount": 90.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None}
                },
                "passengerFlightPriceDetails": None, "bundle": "basic", "fareDiscountType": "none", "wdc": None,
                "distributionFeePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "isFamily": False, "soldOut": False,
                "groupAdministrationFeePrice": {"amount": 0.0, "currencyCode": "PLN", "exchangedAmount": None, "exchangedCurrencyCode": None},
                "promotion": None
            }
        ],
        "infantLimitExceeded": {"limitExceeded": False, "isBlocking": True},
        "wheelchairLimitExceeded": {"unavailableCount": 0, "limitExceeded": False, "isBlocking": False},
        "oxyLimitExceeded": {"limitExceeded": False, "isBlocking": True},
        "sportsEquipmentLimitExceeded": {"unavailableCount": 0, "limitExceeded": False, "isBlocking": False},
        "autoCheckInLimitExceeded": {"unavailableCount": 0, "limitExceeded": False, "isBlocking": False},
        "isRequest": False, "isLease": False, "duration": "02:00:00"
    }

    sample_response = {
        "outboundFlights": [sample_flight_data],
        "returnFlights": [],
        "outboundBundles": [],
        "returnBundles": [],
        "currencyCode": "PLN",
        "arrivalStationCurrencyCode": "EUR",
        "isDomestic": False,
        "isGroup": False,
        "discountType": "none",
        "discountPercentage": 0.0,
        "isBundleCompositionWarningTextVisible": False,
        "isWdcPremiumEnabled": True,
        "isPrivilegePassAllowed": True,
        "isSmartBundleWarningTextVisible": True,
        "isMetaSearchSourceDisableBundleAB": False,
        "isOutboundAirportCheckinFree": False,
        "isReturnAirportCheckinFree": False,
        "var99": False
    }

    response = SearchResponse(**sample_response)
    print(f"\n✓ Parsed search response")
    print(f"  Outbound flights: {len(response.outboundFlights)}")
    print(f"  Return flights: {len(response.returnFlights)}")
    print(f"  Currency: {response.currencyCode}")
    print(f"  Is domestic: {response.isDomestic}")

    cheapest_outbound = response.get_cheapest_outbound()
    if cheapest_outbound:
        fare = cheapest_outbound.get_cheapest_fare()
        print(f"\n✓ Cheapest outbound flight:")
        print(f"  Flight: {cheapest_outbound.flightNumber}")
        print(f"  Price: {fare.basePrice.amount} {fare.basePrice.currencyCode}")

    return response


if __name__ == "__main__":
    test_flight_dates_parsing()
    test_search_response_parsing()
    test_full_search_response()

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
