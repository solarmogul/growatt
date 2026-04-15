<<<<<<< HEAD
# Growatt EMS

Advanced EMS for Growatt + Tesla PW2 + openWB.

## Features
- Night Mode
- Wallbox Mode
- SOC protection
- Tesla suppression

## Install
- Add repo to HACS
- Install integration
- Restart Home Assistant

## 🔌 Modbus Register (Growatt SPH 4600 BL-UP)

Diese Integration wurde mit folgendem System entwickelt und getestet:

- **Inverter:** Growatt SPH 4600 BL-UP  
- **Kommunikation:** Modbus TCP  
- **Unit ID:** 1 (Standard)  
- **Protos PE11 TCP RTU Modbus RS-485 Umsetzer:** 1 (Standard)
- **RS-485-1:PIN 4 = A** 1 (Standard)
- **RS-485-1:PIN 5 = B** 1 (Standard)
- **RS-485-1:PIN 6 = GND** 1 (Standard)

⚠️ **Hinweis:**  
Die verwendeten Register können je nach Firmware oder Modell variieren.  
Bitte bei Abweichungen mit Vorsicht testen.

---

### ⚙️ Betriebsmodi

| Funktion             | Register | Beschreibung                 |
|----------------------|----------|------------------------------|
| Battery First Enable | `1102`   | Aktiviert Batterie-Priorität |
| Battery First Start  | `1100`   | Startzeit (HH:MM encoded)    |
| Battery First End    | `1101`   | Endzeit                      |

| Funktion            | Register | Beschreibung             |
|---------------------|----------|--------------------------|
| Grid First Enable   | `1082`   | Aktiviert Netz-Priorität |
| Grid First Start    | `1080`   | Startzeit                |
| Grid First End      | `1081`   | Endzeit                  |

---

### 🔋 Leistungssteuerung

| Funktion        | Register   | Einheit |
|-----------------|------------|---------|
| Charge Power    | `1090`     | %       |
| Discharge Power | `1070`     | %       |

---

### 📊 Sensorwerte

| Funktion      | Register | Beschreibung    |
|---------------|----------|-----------------|
| Battery SOC   | `1014`   | Ladezustand (%) |

---

### ⏱ Zeitkodierung

Zeitwerte werden wie folgt codiert:

```python
encoded = (hour << 8) | minute
00:00 → 0
23:59 → 0x173B (5947)
=======
# growatt
Growatt EMS for SPH 4600 BL-UP and Tesla PW2
>>>>>>> a20de17369a6ca1f66f7a69cf43ec44bedba4adb
