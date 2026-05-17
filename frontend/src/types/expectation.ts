export interface SectorView {
  sector_name: string
  thesis: string
  confidence: '高' | '中' | '低'
  time_horizon: '短期' | '中期' | '长期'
}

export interface CustomSection {
  title: string
  content: string
}

export interface ExpectationContent {
  policy_long_term: string
  policy_medium_term: string
  policy_short_term: string
  liquidity_assessment: string
  economic_phase: string
  cycle_detail: string
  market_trend: string
  market_phase_detail: string
  sector_views: SectorView[]
  custom_sections: CustomSection[]
}

export interface Expectation {
  _id: string
  id: string
  user_id: string
  title: string
  content: ExpectationContent
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ExpectationCreate {
  title: string
  content: ExpectationContent
}

export interface ExpectationUpdate {
  title?: string
  content?: ExpectationContent
  is_active?: boolean
}
