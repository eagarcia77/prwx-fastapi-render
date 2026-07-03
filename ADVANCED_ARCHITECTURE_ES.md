# Arquitectura avanzada v0.5

```text
NWS API  ─┐
MRMS QPE ─┼─> Control de calidad ─> Features PR ─> Ensamble ML ─> Riesgo operacional ─> Dashboard/API
USGS     ─┤
Alerts   ─┘
```

## Salidas principales

- `corrected_precip_24h_in`
- `precip_p10_in`
- `precip_p90_in`
- `prob_ge_1in`
- `prob_ge_2in`
- `prob_ge_4in`
- `operational_risk_score`
- `impact_level`
- `quality_flag`

## Recomendación operacional

Para mantener el sistema actualizado, usar GitHub Actions cada 3 horas o un servicio cloud que ejecute:

```bash
python scripts/12_operational_update_v5.py
```

Para nowcasting más fuerte, usar una ejecución cada 30 a 60 minutos en una computadora o servidor propio.
