import { Bot, FileText, FlaskConical, Home, Info, MessageCircleQuestion, Upload } from 'lucide-react'

export const NAV = [
  { to: '/', label: 'Home', Icon: Home },
  { to: '/decisions', label: 'Decisions', Icon: FileText },
  { to: '/ask', label: 'Ask why', Icon: MessageCircleQuestion },
  { to: '/ingest', label: 'Ingest', Icon: Upload },
  { to: '/agents', label: 'Agents', Icon: Bot },
  { to: '/benchmark', label: 'Benchmark', Icon: FlaskConical },
  { to: '/about', label: 'About', Icon: Info },
] as const
