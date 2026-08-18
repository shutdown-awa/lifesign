"""Pydantic models for incoming device + health status JSON."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BatteryInfo(BaseModel):
    percentage: int = Field(ge=0, le=100)
    is_charging: bool


class LocationInfo(BaseModel):
    state: Optional[str] = None
    country: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class NetworkInfo(BaseModel):
    is_using_wifi: Optional[bool] = None


class UsageInfo(BaseModel):
    app: Optional[str] = None
    is_not_using: Optional[bool] = None


class DeviceStage(BaseModel):
    network: Optional[NetworkInfo] = None
    usage: Optional[UsageInfo] = None
    location: Optional[LocationInfo] = None
    battery: Optional[BatteryInfo] = None


class StatusInfo(BaseModel):
    """Health status sub-object."""
    is_sleeping: Optional[bool] = None
    activity: Optional[str] = None


class WorkoutInfo(BaseModel):
    steps: Optional[int] = None
    active_calories: Optional[int] = None


class BodyInfo(BaseModel):
    body_temperature: Optional[float] = None
    heart_rate_variability: Optional[int] = None
    heart_beat: Optional[int] = None


class HealthInfo(BaseModel):
    status: Optional[StatusInfo] = None
    workout: Optional[WorkoutInfo] = None
    body: Optional[BodyInfo] = None


class PackageInfo(BaseModel):
    """Upload package metadata (same level as deviceStage / health)."""
    version: Optional[int] = None
    date: Optional[str] = None


class StatusPayload(BaseModel):
    """The full payload sent from the phone."""
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    device_stage: Optional[DeviceStage] = Field(default=None, alias="deviceStage")
    health: Optional[HealthInfo] = None
    package: Optional[PackageInfo] = None