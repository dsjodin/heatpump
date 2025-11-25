# Thermia Värmepump Dashboard - Svensk Version med Sankey

## 🎉 Komplett Dashboard med Energiflödesvisualisering!

Detta är den **kompletta svenska versionen** av Thermia värmepumpsdashboarden med den nya **Sankey energiflödesdiagrammet** som visar exakt hur energin flödar genom din värmepump.

---

## ✨ NYTT: Sankey Energiflödesdiagram

### Vad är det?
En visuell representation av energiflödet genom din värmepump som visar:

```
Mark/Luft (KALL) ──┐
                   ├─> Värmepump ──> Värme till Hus (VARM)
Elkraft (GUL) ─────┘
```

### Varför är det viktigt?
- **Visar COP visuellt**: Du ser direkt hur mycket gratis energi du får från marken
- **Förstå energibalansen**: Hur mycket kommer från el vs mark
- **Färgkodning**: 
  - 🔵 **Blå** = Kall energi från mark/luft
  - 🟡 **Gul** = Elkraft till kompressor
  - 🔴 **Röd** = Tillsattsvärme (om aktiv)
  - 🟠 **Orange** = Varm energi till huset

### Exempel
Om din COP är 3.0:
- För varje **1 kW** el du betalar för
- Får du **3 kW** värme
- **2 kW kommer GRATIS från marken!** (67% gratis)

Detta visar Sankey-diagrammet tydligt med proportionella flöden.

---

## 📊 Alla Features

### 1. **KPI-Kort** (Överst)
- **Medel COP**: Genomsnittlig värmefaktor för vald period
- **Energikostnad**: Total kostnad i SEK för perioden
- **Kompressor**: Hur mycket kompressorn varit igång (%)
- **Tillsattsvärme**: Hur mycket tillsattsvärme använts (%)

### 2. **Temperaturkort** med MIN/MAX
- **Ute**: Utomhustemperatur + min/max för period
- **Inne**: Inomhustemperatur + min/max
- **Varmvatten**: Varmvattentemperatur + min/max
- **Effekt**: Aktuell effektförbrukning + min/max
- **KB In/Ut**: Köldbärare in och ut
- **Fram/Retur**: Radiator framledning och retur

### 3. **Systemstatus**
Badges som visar:
- 🔄 Kompressor (PÅ/AV)
- 🔥 Tillsattsvärme (% eller AV)
- 💧 Köldbärarpump (PÅ/AV)
- 📡 Radiatorpump (PÅ/AV)
- ⚠️ Alarm (om aktiv)

### 4. **✨ SANKEY ENERGIFLÖDE** (NYTT!)
Visuell representation av energiflödet:
- Markenergi → Värmepump
- Elkraft → Värmepump
- Tillsats (om aktiv) → Hus
- Värmepump → Hus
- Visar COP direkt i diagrammet
- Beräknar % gratis energi från marken

### 5. **COP-Graf**
- COP över tiden
- Genomsnittslinje
- Visar värmefaktorns variation

### 6. **Drifttidsanalys** (Cirkeldiagram)
- Kompressor drifttid
- Tillsattsvärme drifttid
- Inaktiv tid

### 7. **Varmvattencykler**
- Totalt antal cykler
- Cykler per dag
- Genomsnittlig varaktighet
- Genomsnittlig energi per cykel

### 8. **Temperaturtrender**
Alla temperaturer i en graf:
- Ute, Inne, Varmvatten
- Radiator fram/retur
- Köldbärare in/ut

### 9. **Systemprestanda**
- Temperaturdifferenser (ΔT) för köldbärare och radiatorer
- Kompressor drifttid över tiden

### 10. **Effektförbrukning**
- Effektförbrukning i W över tiden
- Systemstatus (kompressor + tillsats) över tiden

---

## 🚀 Installation

### Docker (Rekommenderas)

1. **Kopiera filer**:
```bash
# Extrahera arkivet
tar -xzf thermia-dashboard-svenska.tar.gz

# Eller unzip
unzip thermia-dashboard-svenska.zip

# Gå till mappen
cd thermia-dashboard-svenska
```

2. **Starta dashboarden**:
```bash
# Använd din befintliga docker-compose.yml och byt bara dashboard-delen
# Eller kör standalone (kräver InfluxDB):
docker build -t thermia-dashboard .
docker run -p 8050:8050 \
  -e INFLUXDB_URL=http://din-influxdb:8086 \
  -e INFLUXDB_TOKEN=ditt-token \
  -e INFLUXDB_ORG=thermia \
  -e INFLUXDB_BUCKET=heatpump \
  thermia-dashboard
```

3. **Öppna i webbläsare**:
```
http://localhost:8050
```

### Manuell Installation

```bash
# Installera dependencies
pip install -r requirements.txt

# Sätt miljövariabler
export INFLUXDB_URL=http://localhost:8086
export INFLUXDB_TOKEN=your-token
export INFLUXDB_ORG=thermia
export INFLUXDB_BUCKET=heatpump

# Starta dashboard
python app.py
```

---

## 📁 Filstruktur

```
thermia-dashboard-svenska/
├── app.py              # Huvudapplikation (svensk)
├── layout.py           # UI-layout (svensk + Sankey)
├── callbacks.py        # Callbacks (svensk + Sankey)
├── data_query.py       # Data och beräkningar
├── Dockerfile          # Docker build
├── requirements.txt    # Python dependencies
└── assets/
    └── style.css       # CSS styling (Sankey-stöd)
```

---

## ⚙️ Konfiguration

### Tidsintervall
Välj från dropdown:
- ⏰ Senaste timmen
- ⏰ Senaste 6 timmarna
- ⏰ Senaste 24 timmarna
- 📅 Senaste 7 dagarna
- 📅 Senaste 30 dagarna

### Elpris
Ändra elpriset (kr/kWh) för att se korrekt kostnad.

---

## 🎨 Sankey-diagram Detaljer

### Hur beräknas flödena?

1. **Elkraft (gul)**: Baseline på 100 enheter (normaliserat)

2. **Markenergi (blå)**: Beräknas från COP
   ```
   Markenergi = Elkraft × (COP - 1)
   
   Exempel med COP 3.0:
   Markenergi = 100 × (3.0 - 1) = 200 enheter
   ```

3. **Total värme (orange)**: 
   ```
   Total = Elkraft + Markenergi + Tillsats
   
   Exempel:
   Total = 100 + 200 + 0 = 300 enheter
   ```

4. **Gratis energi från marken**:
   ```
   Gratis % = (COP - 1) / COP × 100
   
   Exempel med COP 3.0:
   Gratis % = (3.0 - 1) / 3.0 × 100 = 66.7%
   ```

### Färgkodning

| Färg | Betydelse | Vad det visar |
|------|-----------|---------------|
| 🔵 Blå | Kall energi | Gratis från mark/luft |
| 🟡 Gul | Elkraft | Vad du betalar för |
| 🔴 Röd | Tillsats | Extra elvärme (dyr) |
| 🟢 Grön | Värmepump | Där magin händer |
| 🟠 Orange | Varm energi | Värme till huset |

---

## 📊 Användningsexempel

### Scenario 1: Effektiv drift (COP 4.0)
```
Sankey visar:
─ 100 enheter el (gul)        → du betalar
─ 300 enheter mark (blå)      → GRATIS! (75%)
═ 400 enheter värme (orange)  → till huset

Resultat: 75% gratis värme från marken!
```

### Scenario 2: Kall vinterdag (COP 2.5, tillsats aktiv)
```
Sankey visar:
─ 100 enheter el (gul)        → kompressor
─ 150 enheter mark (blå)      → GRATIS (60%)
─ 50 enheter tillsats (röd)   → dyr elvärme
═ 300 enheter värme (orange)  → till huset

Resultat: 50% gratis från mark, 50% du betalar för
```

### Scenario 3: Mild vårdag (COP 5.0, ingen tillsats)
```
Sankey visar:
─ 100 enheter el (gul)        → minimal elkostnad
─ 400 enheter mark (blå)      → GRATIS! (80%)
═ 500 enheter värme (orange)  → till huset

Resultat: 80% gratis värme - FANTASTISKT!
```

---

## 🔧 Felsökning

### Sankey visar inga data
- Kontrollera att InfluxDB har data
- Verifiera att COP beräknas (kräver köldbärare och radiatortemperaturer)
- Se till att kompressor varit igång under vald period

### Felaktiga flöden
- COP-beräkningen kan variera - det är approximationer
- Sankey använder normaliserade värden för visualisering
- Faktisk energi i kWh finns i KPI-korten

### Dashboard uppdateras inte
- Auto-refresh är 30 sekunder
- Tryck F5 för manuell uppdatering
- Kontrollera InfluxDB-anslutning

---

## 🌟 Jämfört med Original

| Feature | Original | DENNA VERSION |
|---------|----------|---------------|
| Språk | Engelska | ✅ Svenska |
| KPI-kort | ✅ | ✅ |
| Temperaturer | ✅ | ✅ |
| MIN/MAX värden | ✅ | ✅ |
| COP-beräkning | ✅ | ✅ |
| Grafer | ✅ | ✅ |
| **Sankey-diagram** | ❌ | ✅ **NYTT!** |
| Energiflöde | ❌ | ✅ **NYTT!** |
| Visuell COP | ❌ | ✅ **NYTT!** |

---

## 📈 Kommande Features (Fas 3)

- **SPF (Seasonal Performance Factor)**: Årsgenomsnitt COP
- **Värmekurve-analys**: Optimera din värmekurva
- **Prognoser**: AI-baserade värmebehov
- **Intelligenta larm**: Proaktiva varningar
- **Kostnadsoptimering**: Elpris-integration
- **Jämförelser**: Månad-mot-månad

---

## 🤝 Support

Om du har frågor eller problem:
1. Kontrollera [README.md](README.md)
2. Verifiera InfluxDB-anslutning
3. Kolla loggar: `docker logs thermia-dashboard`

---

## 📝 Ändringslogg

### Version 2.0 - Svensk + Sankey (November 2025)
- ✅ Komplett översättning till svenska
- ✅ Sankey energiflödesdiagram
- ✅ Visuell COP-representation
- ✅ Färgkodade energiflöden
- ✅ Förbättrad CSS för Sankey
- ✅ Beräkning av gratis markenergi

### Version 1.0 - Original (November 2025)
- ✅ Grundläggande dashboard
- ✅ KPI-kort
- ✅ Temperaturer och grafer
- ✅ MIN/MAX värden
- ✅ COP-beräkning

---

## 🎉 Lycka Till!

Din värmepump är nu fullständigt övervakad med:
- 📊 Real-time data
- 🇸🇪 Svenska språket
- 🔄 Sankey energiflöde
- 💰 Kostnadsberäkning
- 📈 Prestandaanalys

**Njut av din smarta värmepump! 🔥💚**

---

## 📜 Licens

Detta projekt är för personligt bruk. Dela gärna med andra Thermia-ägare!

---

## 🙏 Tack

Tack för att du använder Thermia Dashboard! 
Om du gillar projektet, sprid gärna ordet till andra värmepumpsägare.

**Varm hälsning,**  
*Thermia Dashboard Team* 🔥
