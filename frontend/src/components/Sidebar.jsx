import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Settings, FileText, Pencil, Clock, LayoutList, ChevronLeft, ChevronRight } from 'lucide-react'
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

const MIN_WIDTH = 60
const EXPANDED_MIN_WIDTH = 160
const MAX_WIDTH_RATIO = 0.3

export default function Sidebar() {
  const { role } = useAuth()
  const { t } = useTranslation()
  const [collapsed, setCollapsed] = useState(false)
  const [width, setWidth] = useState(240)
  const handleRef = useRef(null)

  const items = MENU[role] || []

  useEffect(() => {
    const onMouseMove = (e) => {
      const newWidth = Math.round(e.clientX)
      setWidth(Math.max(MIN_WIDTH, Math.min(newWidth, window.innerWidth * MAX_WIDTH_RATIO)))
    }
    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
    }
    const node = handleRef.current
    const onResizeStart = () => {
      document.addEventListener('mousemove', onMouseMove)
      document.addEventListener('mouseup', onMouseUp)
    }
    if (node) {
      node.addEventListener('mousedown', onResizeStart)
    }
    return () => {
      if (node) {
        node.removeEventListener('mousedown', onResizeStart)
      }
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
    }
  }, [])

  const toggleCollapsed = () => setCollapsed((prev) => !prev)

  const currentWidth = collapsed ? MIN_WIDTH : Math.max(EXPANDED_MIN_WIDTH, Math.min(width, window.innerWidth * MAX_WIDTH_RATIO))

  return (
    <aside className="sidebar" data-collapsed={collapsed} style={{ width: currentWidth }}>
      <div className="sidebar__header">
        <button type="button" className="sidebar__toggle" onClick={toggleCollapsed} aria-label="collapse">
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>
      <nav className="sidebar__menu">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <NavLink key={item.path} to={item.path} className={({ isActive }) => (isActive ? 'sidebar__item sidebar__item--active' : 'sidebar__item')} title={t(item.labelKey)}>
              <Icon size={20} strokeWidth={1.5} />
              <span className="sidebar__label">{t(item.labelKey)}</span>
            </NavLink>
          )
        })}
      </nav>
      <div className="sidebar__footer">
        <hr className="sidebar__divider" />
        <span className="sidebar__logo">Reputa</span>
      </div>
      <div className="sidebar__handle" ref={handleRef} />
    </aside>
  )
}
