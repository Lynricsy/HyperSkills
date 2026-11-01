// server/api/projects/[id].patch.ts
import { renameProject } from '~~/server/utils/projects'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const body = await readBody<{ name?: string }>(event)

  if (!id) {
    throw createError({ statusCode: 400, statusMessage: 'Missing project id' })
  }
  if (!body?.name || body.name.trim().length === 0) {
    throw createError({ statusCode: 422, statusMessage: 'Project name is required' })
  }

  const project = await renameProject(id, body.name.trim())
  if (!project) {
    throw createError({ statusCode: 404, statusMessage: 'Project not found' })
  }
  return project
})
