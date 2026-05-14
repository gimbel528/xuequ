export interface Community {
  id: number
  school_id: number
  name: string
  coordinates: string
}

export interface School {
  id: number
  name: string
  address: string | null
  phone: string | null
  description: string | null
  color: string
  longitude: number | null
  latitude: number | null
  has_district: boolean
  coordinates: string | null
  communities: Community[]
}

export interface SchoolForm {
  name: string
  address: string
  phone: string
  description: string
  color: string
}

export interface District {
  id: number
  school_id: number
  coordinates: string
}

export interface CommunityForm {
  name: string
  coordinates: string
}

export interface ApiResult<T> {
  data: T
  message?: string
}
