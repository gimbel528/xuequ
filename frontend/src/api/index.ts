import axios from 'axios'
import type { School, SchoolForm, District, Community, CommunityForm } from '@/types'

const api = axios.create({
  baseURL: 'https://xuequ-three-vercel.app/api',
  timeout: 30000
})

export const schoolApi = {
  getAll: () => api.get<School[]>('/schools'),
  getById: (id: number) => api.get<School>(`/schools/${id}`),
  create: (data: SchoolForm) => api.post<School>('/schools', data),
  update: (id: number, data: Partial<SchoolForm>) => api.put<School>(`/schools/${id}`, data),
  delete: (id: number) => api.delete(`/schools/${id}`)
}

export const districtApi = {
  getAll: () => api.get<District[]>('/districts'),
  getBySchool: (schoolId: number) => api.get<District>(`/districts/school/${schoolId}`),
  create: (schoolId: number, coordinates: string) => 
    api.post<District>('/districts', { school_id: schoolId, coordinates }),
  update: (schoolId: number, coordinates: string) => 
    api.put<District>(`/districts/school/${schoolId}`, { coordinates }),
  delete: (schoolId: number) => api.delete(`/districts/school/${schoolId}`),
  generateFromCommunities: (schoolId: number, communities: string[]) => 
    api.post(`/districts/generate-from-communities?school_id=${schoolId}`, communities)
}

export const communityApi = {
  getBySchool: (schoolId: number) => api.get<Community[]>(`/communities/school/${schoolId}`),
  create: (schoolId: number, data: CommunityForm) => 
    api.post<Community>(`/communities?school_id=${schoolId}`, data),
  update: (id: number, data: Partial<CommunityForm>) => 
    api.put<Community>(`/communities/${id}`, data),
  delete: (id: number) => api.delete(`/communities/${id}`)
}

export default api
