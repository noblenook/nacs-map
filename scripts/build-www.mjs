// index.html 을 www/ 로 복사하면서 앱 전용 키를 주입합니다.
//  - key.txt (또는 DATA_GO_KR_KEY): 환경부 실시간 충전 상태
//  - kakao_key.txt (또는 KAKAO_KEY): 카카오 장소 검색·경로
// www/ 와 android 의 웹 자산 폴더, 키 파일은 git 에 올라가지 않습니다(.gitignore).
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";

const read = (env, file) => (process.env[env] || (existsSync(file) ? readFileSync(file, "utf8") : "")).trim();
const dataKey = read("DATA_GO_KR_KEY", "key.txt");
const kakaoKey = read("KAKAO_KEY", "kakao_key.txt");

let inject = "";
if (dataKey) inject += `window.NACS_KEY=${JSON.stringify(decodeURIComponent(dataKey))};`;
if (kakaoKey) inject += `window.KAKAO_KEY=${JSON.stringify(kakaoKey)};`;

let html = readFileSync("index.html", "utf8");
if (!html.includes('<script id="app">')) throw new Error('index.html 에 <script id="app"> 가 없습니다');
if (inject) html = html.replace('<script id="app">', `<script>${inject}</script>\n<script id="app">`);
mkdirSync("www", { recursive: true });
writeFileSync("www/index.html", html);
console.log(`www/index.html 생성 · 실시간 상태 키 ${dataKey ? "있음" : "없음"} · 카카오 키 ${kakaoKey ? "있음" : "없음(설정 화면에서 입력)"}`);
