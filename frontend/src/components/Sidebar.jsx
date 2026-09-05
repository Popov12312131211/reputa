import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Settings, FileText, Pencil, Clock, LayoutList } from 'lucide-react'
import { useAuth, ROLES } from '../contexts/AuthContext'
import './Sidebar.css'

const MENU = {
  [ROLES.USER]: [
    { path: '/user/settings', labelKey: 'sidebar.settings', icon: Settings },
    { path: '/user/my', labelKey: 'sidebar.myApplications', icon: FileText },
    { path: '/user/new', labelKey: 'sidebar.newApplication', icon: Pencil },
  ],
  [ROLES.EMPLOYEE]: [
    { path: '/employee/settings', labelKey: 'sidebar.settings', icon: Settings },
    { path: '/employee/newApplication', labelKey: 'sidebar.actualApplications', icon: Clock },
    { path: '/employee/application', labelKey: 'sidebar.allApplications', icon: LayoutList },
  ],
}

// Ширина свёрнутого сайдбара — только колонка иконок.
const COLLAPSED_WIDTH = 64
// Порог перетаскивания: ниже — сайдбар доскальзывает до свёрнутого состояния,
// от порога и выше — до развёрнутого. Между порогом и EXPANDED_MIN_WIDTH
// промежуточных "обрубков" не остаётся.
const COLLAPSE_THRESHOLD = 90
const EXPANDED_MIN_WIDTH = 160
const MAX_WIDTH_RATIO = 0.3

const ICON_SIZE = 20

export default function Sidebar() {
  const { role } = useAuth()
  const { t } = useTranslation()
  const [width, setWidth] = useState(240)
  const [expanded, setExpanded] = useState(true)
  const [dragging, setDragging] = useState(false)
  const handleRef = useRef(null)
  const widthRef = useRef(width)

  const items = MENU[role] || []

  useEffect(() => {
    const onMouseMove = (e) => {
      // Сайдбар начинается в x = 0, поэтому ширина = координате курсора.
      const next = Math.max(8, Math.min(Math.round(e.clientX), Math.round(window.innerWidth * MAX_WIDTH_RATIO)))
      widthRef.current = next
      setWidth(next)
    }
    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      document.body.style.cursor = ''
      // Доскальзывание к ближайшему стабильному состоянию по порогу.
      setExpanded(widthRef.current >= COLLAPSE_THRESHOLD)
      setDragging(false)
    }
    const onResizeStart = () => {
      setDragging(true)
      document.body.style.cursor = 'col-resize'
      document.addEventListener('mousemove', onMouseMove)
      document.addEventListener('mouseup', onMouseUp)
    }
    const node = handleRef.current
    node?.addEventListener('mousedown', onResizeStart)
    return () => {
      node?.removeEventListener('mousedown', onResizeStart)
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      document.body.style.cursor = ''
    }
  }, [])

  const maxWidth = window.innerWidth * MAX_WIDTH_RATIO

  let displayedWidth
  if (dragging) {
    displayedWidth = Math.max(8, Math.min(width, maxWidth))
  } else if (expanded) {
    displayedWidth = Math.max(EXPANDED_MIN_WIDTH, Math.min(width, maxWidth))
  } else {
    displayedWidth = COLLAPSED_WIDTH
  }

  // Во время перетаскивания за порогом визуально уже свёрнуты, но состояние
  // `expanded` меняется только на mouseup — поэтому подписи прячем по факту.
  const collapsed = !expanded || (dragging && width < COLLAPSE_THRESHOLD)

  return (
    <aside
      className={dragging ? 'sidebar sidebar--dragging' : 'sidebar'}
      data-collapsed={collapsed || undefined}
      style={{ width: displayedWidth }}
    >
      <nav className="sidebar__menu">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => (isActive ? 'sidebar__item sidebar__item--active' : 'sidebar__item')}
              title={t(item.labelKey)}
            >
              <Icon size={ICON_SIZE} strokeWidth={1.5} />
              <span className="sidebar__label">{t(item.labelKey)}</span>
            </NavLink>
          )
        })}
      </nav>
      <div className="sidebar__footer">
        <hr className="sidebar__divider" />
        <span className="sidebar__logo">Reputa</span>
      </div>
      {/* Перетаскиваемая правая граница — та же видимая разделительная линия. */}
      <div className="sidebar__handle" ref={handleRef} aria-hidden="true" />
    </aside>
  )
}