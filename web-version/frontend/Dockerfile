# base image - 설정과 공통 의존성 설치
FROM node:18-alpine AS base

WORKDIR /app

# npm-force-resolutions 사용을 위해 필요한 파일들 복사
COPY package.json package-lock.json ./

# npm-force-resolutions 설치 및 실행 (resolutions 적용)
RUN npm install --save-dev npm-force-resolutions \
 && npx npm-force-resolutions \
 && npm install --only=production --legacy-peer-deps \
 && npm cache clean --force

# development stage
FROM node:18-alpine AS development

WORKDIR /app

# 패키지 정보 및 의존성 설치
COPY package.json package-lock.json ./
RUN npm install --save-dev npm-force-resolutions \
 && npx npm-force-resolutions \
 && npm install --legacy-peer-deps

# 전체 소스 복사
COPY . .

EXPOSE 3000
CMD ["npm", "start"]

# build stage
FROM base AS build

# 빌드 시 필요한 환경 변수 (빌드 시점에 주입됨)
ARG REACT_APP_SUPABASE_URL
ARG REACT_APP_SUPABASE_ANON_KEY

# 소스코드 복사
COPY . .

# .env 파일이 없는 경우를 위한 환경 변수 설정
ENV REACT_APP_SUPABASE_URL=$REACT_APP_SUPABASE_URL
ENV REACT_APP_SUPABASE_ANON_KEY=$REACT_APP_SUPABASE_ANON_KEY

# 개발 의존성 포함 재설치 + resolutions 적용
RUN npm install --save-dev npm-force-resolutions \
 && npx npm-force-resolutions \
 && npm install --legacy-peer-deps

# 빌드 실행
RUN npm run build

# production stage
FROM nginx:alpine AS production

# 빌드된 정적 파일을 nginx에 복사
COPY --from=build /app/build /usr/share/nginx/html

# nginx 설정 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]