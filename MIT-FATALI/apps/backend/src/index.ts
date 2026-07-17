import Fastify from 'fastify'
import cors from '@fastify/cors'
import formbody from '@fastify/formbody'
import dotenv from 'dotenv'

dotenv.config()

const server = Fastify({ logger: true })
server.register(cors)
server.register(formbody)

server.get('/', async () => ({ ok: true, service: 'MIT-FATALI backend' }))

// Simple health
server.get('/health', async () => ({ status: 'ok' }))

// Lessons stub
server.get('/lessons', async () => ({ lessons: [{ id: 'l1', title: 'Budgeting 101' }] }))

// Submissions stub
server.post('/submissions', async (request, reply) => {
  // In real app: handle multipart and store image
  return reply.code(201).send({ id: 's1', status: 'pending' })
})

// Payments initiate stub
server.post('/payments/initiate', async (request, reply) => {
  // Validate and call payment adapter
  return { payment_id: 'p1', status: 'pending' }
})

const start = async () => {
  try {
    await server.listen({ port: +(process.env.PORT || 4000), host: '0.0.0.0' })
  } catch (err) {
    server.log.error(err)
    process.exit(1)
  }
}
start()
