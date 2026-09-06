import { useTranslation } from 'react-i18next'
import './ScoreGauge.css'

// COMP-002: спидометр «Благонадёжность (0–100)».
// Чистый SVG без сторонних библиотек. Один пропс — числовое значение 0–100;
// положение и наклон маркера, цвет числа и точки вычисляются внутри
// компонента из этого значения.
//
// Решение продукта: синяя дуга-заливка прогресса УДАЛЕНА (перегружала вид),
// остаётся статичная цветная 3-зонная шкала + риска-маркер значения.
//
// Геометрия: центр дуги (CX, CY), радиус R (средняя линия кольца).
// ratio 0 → крайняя левая точка дуги, ratio 1 → крайняя правая, через верх.
const CX = 240
const CY = 235
const R = 175
const MARKER_HALF = 19
const TICK_IN_RADIUS = R + 14
const TICK_OUT_RADIUS = R + 26
const LABEL_RADIUS = R + 38

// Зоны шкалы (доли дуги) и границы диапазонов числа — симметричны:
// низкая 0–39 (<40), средняя 40–69 (<70), высокая 70–100.
const LOW_MAX = 40
const MID_MAX = 70

const ZONES = [
  { from: 0.0, to: 0.4, tone: 'low' },
  { from: 0.4, to: 0.7, tone: 'mid' },
  { from: 0.7, to: 1.0, tone: 'high' },
]

const SCALE_STEPS = [0, 20, 40, 60, 80, 100]

function pointOnArc(ratio, radius) {
  // ratio 0..1: угол от 180° (лево) до 0° (право) через 90° (верх).
  // angleDeg — полярный угол точки на дуге, он же нужен для наклона маркера.
  const angleDeg = (1 - ratio) * 180
  const angleRad = (angleDeg * Math.PI) / 180
  return {
    x: CX + radius * Math.cos(angleRad),
    y: CY - radius * Math.sin(angleRad),
    angleDeg,
  }
}

function arcPath(fromRatio, toRatio) {
  const start = pointOnArc(fromRatio, R)
  const end = pointOnArc(toRatio, R)
  // Дуга всегда лежит в верхней полуокружности (span ≤ 180°),
  // поэтому large-arc-flag всегда 0; sweep=1 идёт через верхнюю точку.
  // При large-arc=1 (span > 180°) SVG оборачивает дугу вокруг низа — «петля».
  return `M ${start.x} ${start.y} A ${R} ${R} 0 0 1 ${end.x} ${end.y}`
}

export default function ScoreGauge({ value }) {
  const { t } = useTranslation()
  const clamped = value == null ? null : Math.min(100, Math.max(0, value))
  const ratio = clamped == null ? 0 : clamped / 100
  const tone =
    clamped == null
      ? null
      : clamped < LOW_MAX
        ? 'low'
        : clamped < MID_MAX
          ? 'mid'
          : 'high'
  const marker = pointOnArc(ratio, R)

  return (
    <div className="gauge">
      <span className="gauge__title">{t('scoreGauge.title')}</span>
      <svg
        className="gauge__svg"
        viewBox="0 0 480 350"
        role="img"
        aria-label={t('scoreGauge.title')}
      >
        {/* статичная цветная подложка из трёх зон (красная/жёлтая/зелёная),
            всегда видна на всю шкалу 0–100. Заливка прогресса удалена —
            прогресс показывает только риска-маркер. */}
        {ZONES.map((zone) => (
          <path
            key={zone.tone}
            className={`gauge__zone gauge__zone--${zone.tone}`}
            d={arcPath(zone.from, zone.to)}
          />
        ))}

        {/* красная риска-маркер на дуге. Развёрнута вдоль радиуса: та же
            формула, что позиционирует точку (angleDeg), повёрнута на
            (90° − angleDeg), чтобы палочка легла по радиусу, а не стояла
            вертикально; rotate идёт вокруг самой точки маркера.
            Цвет риски — как у зоны, в которой лежит значение (low/mid/high). */}
        {clamped != null && (
          <line
            className={`gauge__marker gauge__marker--${tone}`}
            x1={marker.x}
            y1={marker.y - MARKER_HALF}
            x2={marker.x}
            y2={marker.y + MARKER_HALF}
            transform={`rotate(${90 - marker.angleDeg} ${marker.x} ${marker.y})`}
          />
        )}

        {/* деления шкалы: риски + подписи в точках 0, 20, 40, 60, 80, 100 */}
        {SCALE_STEPS.map((step) => {
          const inner = pointOnArc(step / 100, TICK_IN_RADIUS)
          const outer = pointOnArc(step / 100, TICK_OUT_RADIUS)
          const label = pointOnArc(step / 100, LABEL_RADIUS)
          return (
            <g key={step}>
              <line
                className="gauge__tick"
                x1={inner.x}
                y1={inner.y}
                x2={outer.x}
                y2={outer.y}
              />
              <text className="gauge__tick-label" x={label.x} y={label.y} textAnchor="middle">
                {step}
              </text>
            </g>
          )
        })}

        {/* крупное значение по центру под дугой + точка-индикатор */}
        <text
          className={`gauge__number${tone ? ` gauge__number--${tone}` : ''}`}
          x={CX}
          y={CY + 72}
          textAnchor="middle"
        >
          {clamped != null ? clamped : '—'}
        </text>
        {clamped != null && (
          <circle className={`gauge__dot gauge__dot--${tone}`} cx={CX} cy={CY + 94} r={5} />
        )}
      </svg>
    </div>
  )
}