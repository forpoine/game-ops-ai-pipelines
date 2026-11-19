# baseline 오답 유형 (용어집 없이 번역, n=40)

- match: 공식 표기가 들어감 / english_kept: 영어 이름을 그대로 둠 / other: 다른 말로 옮김(직역·음역 등) / empty: 빈 출력

## ko

| 모델 | match | english_kept | other | empty |
|---|---|---|---|---|
| Gemma 12B | 7 | 0 | 32 | 1 |
| gpt-oss 20B | 3 | 2 | 35 | 0 |
| Qwen3 14B | 1 | 2 | 37 | 0 |

## ja

| 모델 | match | english_kept | other | empty |
|---|---|---|---|---|
| Gemma 12B | 3 | 0 | 36 | 1 |
| gpt-oss 20B | 2 | 3 | 35 | 0 |
| Qwen3 14B | 1 | 1 | 38 | 0 |

## es

| 모델 | match | english_kept | other | empty |
|---|---|---|---|---|
| Gemma 12B | 14 | 10 | 15 | 1 |
| gpt-oss 20B | 17 | 19 | 4 | 0 |
| Qwen3 14B | 17 | 14 | 9 | 0 |

## 예시: 같은 문장, 세 모델의 한국어/일본어 출력 (아이템 8개)

**Use a Swift Mochi before the boss fight to recover your HP.**  공식: ko `순발력떡` / ja `しゅんぱつのもち` / es `Mochi Ímpetu`

- Gemma 12B: ko X `보스전 전에 신속 모찌를 사용하여 HP를 회복하세요.` | ja X `ボス戦の前にスイフト餅を使ってHPを回復しましょう。`
- gpt-oss 20B: ko X `보스 전투 전에 스위프트 모치를 사용해 체력을 회복하세요.` | ja X `ボス戦前にSwift Mochiを使用してHPを回復してください。`
- Qwen3 14B: ko X `보스 전투 시작 전에 스위프트 모치를 사용하여 HP를 회복하세요.` | ja X `ボス戦が始まる前にスイフトモチを使用してHPを回復してください。`

**The drop rate of Iron has been increased during the event.**  공식: ko `사포닌` / ja `ブロムヘキシン` / es `Hierro`

- Gemma 12B: ko X `이벤트 기간 동안 철의 드롭률이 증가했습니다.` | ja X `イベント期間中、鉄のドロップ率が上昇しました。`
- gpt-oss 20B: ko X `이벤트 기간 동안 철의 드롭률이 증가했습니다.` | ja X `イベント中に鉄のドロップ率が上昇しました。`
- Qwen3 14B: ko X `이벤트 기간 동안 철의 드롭률이 증가했습니다.` | ja X `イベント期間中、鉄のドロップ率が上昇しました。`

**The drop rate of Lure has been increased during the event.**  공식: ko `벌레유인코롱` / ja `むしよせコロン` / es `Colonia`

- Gemma 12B: ko X `이벤트 기간 동안 루어의 드랍률이 상향되었습니다.` | ja X `イベント期間中、ルアーのドロップ率が上昇しました。`
- gpt-oss 20B: ko X `이벤트 기간 동안 루어의 드롭률이 증가되었습니다.` | ja X `イベント中にルアーのドロップ率が上昇しました。`
- Qwen3 14B: ko X `이벤트 기간 동안 루어의 드롭률이 증가했습니다.` | ja X `イベント期間中、ルアのドロップ率が上昇しました。`

**Players can buy a Sweet Heart at the shop for 200 coins.**  공식: ko `하트스위트` / ja `ハートスイーツ` / es `Corazón Dulce`

- Gemma 12B: ko X `상점에서 200 코인으로 스위트 하트를 구매할 수 있습니다.` | ja X `ショップで200コインでスウィートハートを購入できます。`
- gpt-oss 20B: ko X `플레이어는 상점에서 스위트 하트를 200코인으로 구매할 수 있습니다.` | ja X `プレイヤーはショップでスイートハートを200コインで購入できます。`
- Qwen3 14B: ko X `플레이어는 상점에서 200개의 동전으로 스위트 하트를 구매할 수 있습니다.` | ja X `プレイヤーはショップで200枚のコインを使ってスイートハートを購入できます。`

**Each trainer receives one Full Heal as a login reward.**  공식: ko `만병통치제` / ja `なんでもなおし` / es `Cura Total`

- Gemma 12B: ko X `모든 트레이너는 로그인 보상으로 풀 힐 1개를 받습니다.` | ja X `各トレーナーはログイン報酬としてフルヒールを1つ獲得できます。`
- gpt-oss 20B: ko X `각 트레이너는 로그인 보상으로 한 개의 풀 힐을 받습니다.` | ja X `各トレーナーはログイン報酬として1つのフルヒールを受け取ります。`
- Qwen3 14B: ko X `각 트레이너는 로그인 보상으로 하나의 풀 힐을 받습니다.` | ja X `各トレーナーはログイン報酬としてフルヒールを1つ受け取ります。`

**Use a Leppa Berry before the boss fight to recover your HP.**  공식: ko `과사열매` / ja `ヒメリのみ` / es `Baya Zanama`

- Gemma 12B: ko X `보스전 전에 레파 베리를 사용하여 HP를 회복하세요.` | ja X `ボス戦の前にレッパベリーを使ってHPを回復してください。`
- gpt-oss 20B: ko X `보스 전투 전에 레파 베리(Leppa Berry)를 사용해 체력을 회복하세요.` | ja X `ボス戦前にレッパベリーを使ってHPを回復してください。`
- Qwen3 14B: ko X `보스 전투 시작 전에 레파 베리 사용으로 HP를 회복하세요.` | ja X `ボス戦が始まる前にレパーベリーを使用してHPを回復してください。`

**The drop rate of Shalour Sable has been increased during the event.**  공식: ko `사라사블레` / ja `シャラサブレ` / es `Galleta Yantra`

- Gemma 12B: ko X `이벤트 기간 동안 샬루르 세이블의 드롭률이 증가했습니다.` | ja X `イベント期間中、シャルール・セーブルのドロップ率が上昇しました。`
- gpt-oss 20B: ko X `이벤트 기간 동안 샬루르 새블의 드롭률이 상승했습니다.` | ja X `イベント中にシャルール・サーブルのドロップ率が上昇しました。`
- Qwen3 14B: ko X `이벤트 기간 동안 샤LOUR 사블의 드롭률이 증가했습니다.` | ja X `イベント期間中、シャラウ・サブルのドロップ率が上昇しています。`

**Use a Fluffy Tail before the boss fight to recover your HP.**  공식: ko `에나비꼬리` / ja `エネコのシッポ` / es `Cola Skitty`

- Gemma 12B: ko X `보스전 전에 푹신한 꼬리를 사용하여 HP를 회복하세요.` | ja X `ボス戦の前に「ふわふわのしっぽ」を使ってHPを回復しましょう。`
- gpt-oss 20B: ko X `보스 전투 전에 플러피 테일을 사용해 체력을 회복하세요.` | ja X `ボス戦前にフラッフィーテイルを使用してHPを回復してください。`
- Qwen3 14B: ko X `보스 전투 시작 전에 푹신한 꼬리를 사용하여 HP를 회복하세요.` | ja X `ボス戦が始まる前にフワフワテールを使用してHPを回復してください。`
