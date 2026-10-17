import {
  Activity,
  BarChart3,
  BatteryCharging,
  LayoutDashboard,
  MapPin,
  Settings2,
  Zap,
} from 'lucide-react'

export const navigationItems = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    description:
      'A unified view of your EV charging network, operational health, and business performance.',
    icon: LayoutDashboard,
  },
  {
    label: 'Charging Stations',
    path: '/stations',
    description:
      'Manage your charging locations and get a clear view of the station network.',
    icon: MapPin,
  },
  {
    label: 'Chargers',
    path: '/chargers',
    description:
      'Review charger inventory, availability, and operational status.',
    icon: BatteryCharging,
  },
  {
    label: 'Energy Monitoring',
    path: '/energy',
    description:
      'Monitor energy usage and charging demand across your network.',
    icon: Zap,
  },
  {
    label: 'Business Analytics',
    path: '/analytics',
    description:
      'Explore business performance and insights from your charging operations.',
    icon: BarChart3,
  },
  {
    label: 'Charging Sessions',
    path: '/sessions',
    description:
      'Review charging sessions and activity across your network.',
    icon: Activity,
  },
  {
    label: 'Settings',
    path: '/settings',
    description:
      'Configure workspace preferences and platform settings.',
    icon: Settings2,
  },
]
