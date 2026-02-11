import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = { vus: 1, duration: '30s' };

export default function () {
  const base = __ENV.BASE_URL || 'http://localhost:8000';
  const res = http.get(`${base}/weather/seattle`);
  check(res, { 'status is 200 or 503': (r) => r.status === 200 || r.status === 503 });
  sleep(1);
}
