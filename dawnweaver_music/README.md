# Dawn Weaver 戦闘音楽（自作合成版）

| ファイル | 曲名 | 調 / テンポ | 長さ | 用途 |
|---|---|---|---|---|
| `out/dawnweaver_battle_normal_loop.*` | 朝霧を織る刃 | ニ短調 / 156 BPM / 4拍子 / 24小節 | 36.92秒 | 通常戦闘（ループ） |
| `out/dawnweaver_battle_boss_loop.*` | 黎明を喰らうもの | ハ短調 / 172 BPM / 4拍子（3+3+2）/ 32小節 | 44.65秒 | ボス戦（ループ） |
| `out/dawnweaver_battle_violin_loop.*` | 糸車の剣舞 | イ短調 / 168 BPM / 4拍子 / 24小節 | 34.29秒 | 戦闘・バイオリン主役（ループ） |
| `out/dawnweaver_battle_guitar_loop.*` | 灰の峠を駆ける | ホ短調 / 160 BPM / 4拍子 / 24小節 | 36.00秒 | 戦闘・エレキギター主役（ループ） |
| `out/dawnweaver_battle_violin_real_loop.*` | 糸車の剣舞（生録音版） | イ短調 / 168 BPM / 4拍子 / 24小節 | 34.29秒 | 戦闘・バイオリン主役（ループ、実録音の弦） |
| `out/dawnweaver_victory_fanfare.*` | 夜明けの糸 | ニ長調 / 132 BPM / 3小節 + 余韻 | 8.45秒 | 戦闘勝利（1回再生） |

- 音源はすべて `synth.py` の numpy 合成（サンプル・外部生成サービス不使用）。`python songs.py`（通常・ボス・勝利）と `python songs2.py`（バイオリン・ギター）で再生成できます。
- ループ曲は WAV の先頭〜末尾がそのままループ周期です（残響を周期に折り返し加算済み、フェードなし）。MP3 はエンコーダ遅延で継ぎ目がずれるので、ゲームのループ再生には WAV か OGG を推奨。
- MIDI（`.mid`）は同じ譜面データから書き出したもので、別の音源で鳴らし直す用です。
- 音量: 通常 −10.9 LUFS / ボス −12.6 LUFS / 勝利 −11.3 LUFS、ピーク −1 dBFS 付近。

## 生録音版（`violin_real.py`）

- 音源: [VSCO 2 Community Edition](https://github.com/sgossner/VSCO-2-CE)（CC0 1.0）。ソロバイオリン（アルコ / スピッカート）、バイオリン・ビオラ・チェロ各セクション、コントラバス、ハープ、ティンパニ、大太鼓、スネア、シンバル、タンバリンの実録音を使用。
- 生成: `VSCO_DIR=<VSCO 2 CEのパス> python violin_real.py`（`sampler.py` が読み込み）。
- VSCO 2 CE のファイル名の音名は弦セクションなどで1オクターブ低く表記されているため、各サンプルの音高を測定し、フォルダごとに多数決でオクターブを補正（結果は `vsco_pitch_cache.json`）。
- ティンパニは一番低いドラム（実測 約89.5Hz ≒ F2）だけを使い、F2〜C3 の狭い範囲で移調。
