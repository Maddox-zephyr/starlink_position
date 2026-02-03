# PredictWind DataHub → Chartplotter / OpenCPN / Navionics Setup (Starlink Positioning)

This document describes how to use **Starlink position data** via the **PredictWind DataHub**
as an alternative navigation position source when GNSS is unavailable, degraded, or spoofed.

The DataHub converts Starlink position data into standard **NMEA 0183** and **NMEA 2000**
messages, making them usable by:

- Chartplotters (Raymarine, etc.)
- OpenCPN
- Navionics (mobile)
- Other NMEA-capable navigation software

> ⚠️ **Important disclaimer**  
> Starlink positioning and DataHub-derived GPS data are **not certified as primary navigation sources**.
> This setup is intended as a **fallback / resilience option** only.
> Always cross-check position data and revert to certified GNSS sources as soon as possible.

---

## 1. Overview – Data Flow Options

The PredictWind DataHub can distribute Starlink position data in **two parallel ways**:

### 1.1 Over Wi-Fi (NMEA 0183)
- UDP (recommended for most apps)
- TCP (supported by some apps)
- Used by:
  - OpenCPN
  - Navionics
  - Other mobile or desktop apps

### 1.2 Over the Navigation Backbone (NMEA 2000)
- DataHub → **NMEA2000**
- Can be bridged to:
  - **SeatalkNG**
  - **Seatalk1** (via Raymarine converters)
- Used by:
  - Chartplotters (MFDs)
  - Autopilots
  - Instruments

Both methods can be active simultaneously.

---

## 2. Pre-Requisites

- PredictWind **DataHub** (Pro model required)
- PredictWind **Professional subscription**
- Starlink (Mini tested, other generations expected to behave similarly)
- Starlink configured to expose position data on the **local network** and to **use Startlink positioning exclusively**
  - See: [Starlink setup](starlink_setup.md) for details

---

## 3. DataHub Firmware Update (Required)

Starlink positioning support requires **DataHub firmware v4.41 (beta)**.

### Steps
1. Login to the DataHub web interface
2. Navigate to: Services → Settings → Software Update
3. Select **Alternate**
4. Upgrade to **v4.41** or later

You should see in the changelog: 
  Starlink infrastructure
  > ℹ️ This feature is currently available only to **PredictWind Pro users**.
  > DataHub Pro hardware is required due to increased memory and CPU usage.

![IMAGE:_DataHub Alternate SW update](images/DH_Alternate_Update.jpg)
(DataHub alternate download)
---

## 4. Enable Starlink GPS in DataHub

After updating:
1. Go to: Internet → Starlink
2. Enable **GPS via Starlink**
3. Click **Save & Apply**

![IMAGE: DataHub Internet → Starlink → GPS via Starlink enabled](images/DH_GPS_via_Starlink.jpg)
(Make/Model: PredictWind DataHub, firmware v4.41)

4. Then go to: NMEA → Source
5. Select **Position via Statlink**
6. Click **Save & Apply**

![IMAGE: DataHub NMEA → Source → Position via Startlink selected](images/DH_Nmea_Source_via_Startlink.jpg)
(Make/Model: PredictWind DataHub, firmware v4.41)

---

## 5. Advanced Starlink GPS Tuning (New)

Recent DataHub updates introduce **advanced tuning options**:

### 5.1 Poll Rate
- Range: 2–10 seconds
- Controls how often the DataHub queries the Starlink dish
- Lower = more responsive, higher CPU/network usage

### 5.2 Window Size
- Number of samples used to compute averages
- Affects COG/SOG stability
- Larger values = smoother output, more lag

### 5.3 Smoothing Factor
- Range: 0.0 – 1.0
- Exponential smoothing applied to track output
- Higher = smoother, but increased latency

**Recommended starting values:**
- Poll Rate: `3`
- Window Size: `5`
- Smoothing Factor: `0.3`

> ⚠️ Excessive smoothing may delay turns and course changes.

[IMAGE: DataHub Starlink GPS Advanced Options – Poll Rate / Window Size / Smoothing](images/DH_GPS_via_Startlink_Advanced.jpg)
(Make/Model: PredictWind DataHub)

---

## 6. Chartplotter Configuration

### 6.1 Modern Chartplotters (GPS Source Selection)

Some MFDs (e.g. Raymarine Axiom series) allow manual GPS source selection.

Select: GPS Source → DataHub (RDSensing)

### Image placeholder
[IMAGE: Raymarine Axiom Pro – GPS source selection showing DataHub]
(Make/Model: Raymarine Axiom Pro)


---

### 6.2 Legacy Chartplotters (No GPS Source Selection)

Older chartplotters (e.g. **Raymarine E120 Classic**) do **not** allow GPS source selection.

In this case:
- All other GPS sources **must be disconnected or disabled**
- This includes:
  - Internal GPS
  - AIS GPS feed
  - External GPS sensors

The chartplotter will then automatically use the **only available source**: DataHub → Starlink.

#### Example: GPS lost before enabling DataHub

[IMAGE: GPS Status – Position Fix Lost]
(Make/Model: Raymarine E120 Wide Classic)


#### Example: Fix restored via DataHub / Starlink
[IMAGE: GPS Status – Fix, coordinates, HDOP from DataHub]
(Make/Model: Raymarine E120 Wide Classic)


---

## 7. DataHub → Navigation Backbone (NMEA2000 / Seatalk)

When connected to the navigation backbone, the DataHub injects GNSS data into:

- NMEA2000
- SeatalkNG
- Seatalk1 (via converter)

This allows **full system integration**, including:
- Chartplotters
- Autopilots
- Wind instruments
- Log / speed calculations

---

## 8. OpenCPN Configuration (Step-by-Step)

### 8.1 Network Setup
- Ensure your device is connected to the **DataHub Wi-Fi**
- **Not** the Starlink Wi-Fi

[IMAGE: Mobile device connected to DataHub Wi-Fi (not Starlink)]


---

### 8.2 Add Network Connection

1. Open OpenCPN
2. Go to: Options → Connections
3. Add a new connection:
  - Protocol: **UDP** (recommended)
  - Address: 0.0.0.0
  - Port: `11101`
  - Input only
  - Enable

  OR
  - Protocol: **TCP** (alternative)
  - Address: 10.10.10.1
  - Port: `11102`
  - Input only
  - Enable

[IMAGE: OpenCPN – Network connection settings]


---

### 8.3 Disable Internal GPS (Recommended)

- Uncheck **Built-in GPS** in OpenCPN  
  **OR**
- Disable phone/tablet **Location Services**

This ensures OpenCPN uses **only Starlink-derived position data**.

[IMAGE: OpenCPN – Built-in GPS disabled]


---

## 9. Navionics Configuration (Mobile)

Navionics supports **external GPS sources over Wi-Fi**, but with limitations.

### Key points:
- Navionics **cannot disable a paired device**
- An active connection **cannot be forgotten**
- You must break the connection (disable Wi-Fi or DataHub) to remove it

### Steps:
1. Connect device to **DataHub Wi-Fi**
2. Pair the DataHub GPS source
3. Disable phone **Location Services**
4. Restart Navionics

[IMAGE: Navionics – External GPS receiving data]

[IMAGE: Navionics – External GPS receiving data]


### Example: Before DataHub activation
[IMAGE: Navionics – GPS not enabled]


### Example: Using Starlink positioning
[IMAGE: Navionics – Track, SOG, COG via DataHub/Starlink]


---

## 10. Technical Details – NMEA Sentences & PGNs

### 10.1 NMEA 0183 (Wi-Fi – UDP/TCP)

The DataHub outputs:
- `RMC` – Recommended Minimum Navigation Data
- `GGA` – Fix data
- `GLL` – Geographic position

These are consumed by:
- OpenCPN
- Navionics
- Mobile navigation apps

Update rate:
- Internal dish polling: configurable (2–10s)
- Output rate: **1 Hz**
- Intermediate values use **dead-reckoning interpolation**

---

### 10.2 NMEA 2000 PGNs (Backbone)

The following PGNs are transmitted:

| PGN     | Description |
|--------:|-------------|
| 129029  | GNSS Position Data |
| 129025  | Position, Rapid Update |
| 129026  | COG & SOG, Rapid Update |
| 129033  | Local Time Offset |
| 126992  | System Time |

> **Note:** PGN 129033 is particularly useful for **older Raymarine systems**
> that rely on network-provided time information.

---

## 11. Operational Notes & Best Practices

- Use **Starlink Positioning Exclusively** in the Starlink app when GPS spoofing is suspected
- Always compare position with:
  - Radar
  - Visual fixes
  - Depth contours
- Switch back to certified GNSS when stable

---

## 12. Summary

This setup provides a **robust, multi-path fallback navigation solution** using:

- Starlink positioning
- PredictWind DataHub
- Standard NMEA interfaces

It has been tested on:
- Modern and legacy chartplotters
- OpenCPN
- Navionics mobile apps

While not a replacement for certified GNSS, it significantly improves
navigation resilience in GPS-challenged environments.

---



