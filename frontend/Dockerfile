# syntax=docker/dockerfile:1

FROM node:24-alpine AS base
RUN corepack enable

FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./
RUN pnpm install --frozen-lockfile

FROM base AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["pnpm", "dev"]

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# NEXT_PUBLIC_* vars are baked into the client JS bundle at build time, not read at runtime —
# must be explicitly declared as a build ARG and promoted to a real env var here, otherwise
# `next build` sees it as unset regardless of what's configured on the Railway service, and
# ARG also makes this layer's Docker cache key depend on the value so changing it actually
# triggers a rebuild instead of silently reusing a stale bundle.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN pnpm build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
# corepack re-verifies the lockfile's supply-chain policy (pnpm-workspace.yaml's allowBuilds)
# on every `pnpm` invocation, including `pnpm start` below — without this file present at
# runtime it can't see that policy and falls back to blocking sharp/unrs-resolver's install
# scripts, crashing the container even though the build itself succeeded.
COPY --from=builder /app/pnpm-workspace.yaml ./pnpm-workspace.yaml
COPY --from=builder /app/pnpm-lock.yaml ./pnpm-lock.yaml
EXPOSE 3000
CMD ["pnpm", "start"]
