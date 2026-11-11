// index.html 을 www/ 로 복사하면서, key.txt 가 있으면 앱 전용 실시간 상태 조회용 키를 주입합니다.
// www/ 와 android 의 웹 자산 폴더는 git 에 올라가지 않습니다(.gitignore).
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";

const key = (process.env.DATA_GO_KR_KEY || (existsSync("key.txt") ? readFileSync("key.txt", "utf8") : "")).trim();
let html = readFileSync("index.html", "utf8");
const inject = key ? `<script>window.NACS_KEY=${JSON.stringify(decodeURIComponent(key))};</script>\n` : "";
html = html.replace(/<script>\r?\n\/\/ 환경부 API stat 코드/, m => inject + m);
mkdirSync("www", { recursive: true });
writeFileSync("www/index.html", html);
console.log(key ? "www/index.html 생성 (실시간 상태 키 포함)" : "www/index.html 생성 (키 없음: 10분 단위 데이터만 사용)");
