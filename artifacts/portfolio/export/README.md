# Экспорт диаграмм для слайдов

Исходники правды — Markdown/BPMN в `diagrams/`. Здесь — растровые/векторные копии для презентации.

Повторный экспорт:

```powershell
cd artifacts/portfolio/export
python export_mermaid.py
```

Скрипт пишет `.mmd` и тянет SVG/PNG с [mermaid.ink](https://mermaid.ink). Если сеть режет сервис — откройте `mmd/*.mmd` в [mermaid.live](https://mermaid.live) и Save as SVG/PNG.

BPMN: импорт [diagrams/bpmn-002.bpmn](../../../diagrams/bpmn-002.bpmn) в [bpmn.io](https://demo.bpmn.io/) → Export as SVG.
