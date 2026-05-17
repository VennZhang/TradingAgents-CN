export interface IndexMetadata {
  code: string
  name: string
  display: string
  market: string
  futures: string
}

export interface PredictionRequest {
  expectation_id?: string
  target_indices: string[]
  research_depth: string
  selected_analysts: string[]
  quick_analysis_model?: string
  deep_analysis_model?: string
  analysis_date?: string
}

export interface PredictionTask {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  research_depth?: string
  result?: PredictionResult | null
  error?: string | null
  elapsed_seconds?: number
  created_at: string
}

export interface TaskStatusResponse {
  task_id: string
  status: string
  progress: number
  current_step?: string
  current_step_description?: string
  elapsed_seconds: number
  estimated_remaining_seconds?: number
}

export interface PredictionResult {
  final_index_decision: string
  index_trading_plan: string
  index_investment_plan: string
  index_technical_report: string
  index_sentiment_report: string
  macro_policy_report: string
  index_valuation_report: string
  sector_theme_report: string
  index_impact_report: string
}

export interface SectorInfo {
  sector_code: string
  sector_name: string
  source: string
}

export interface DepthLevel {
  id: number
  name: string
  desc: string
  time: string
  icon: string
}
