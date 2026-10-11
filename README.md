# tavern-card-lint

**Validate SillyTavern / TavernAI character cards before your roleplay breaks.**

角色卡发出去之前体检一遍：起不来场、世界书条目永不触发、字段类型写错——这些都是收到卡的人才发现的坑。

## What it checks

| 级别 | 检查项 |
|---|---|
| error | name / description / first_mes 为空（卡无法正常开场） |
| error | `alternate_greetings` 不是列表、`character_book` 不是对象 |
| warning | personality / scenario / mes_example 为空（推荐填写） |
| warning | 世界书条目没有 keys（**永远不触发**，最常见的废条目来源） |
| warning | 世界书条目 content 为空 |

支持 V2/V3 卡（PNG 内嵌 `chara` / `ccv3` tEXt chunk）。

## Usage

```bash
python tavern_card_lint.py character.png
python tavern_card_lint.py *.png --json report.json   # 批量 + 导出
python tavern_card_lint.py pack/*.png -q              # 只看有问题的
```

输出：

```
[warning] character_book: entry 3 ('hidden lore') has no keys - it can never trigger
(character.png: 0 errors, 1 warnings)
```

发现 error 时退出码 1，适合挂进发卡前的检查流程。

## How it works

PNG 是带 CRC 的 chunk 结构，`tEXt` chunk 存 `keyword\0text` 对。SillyTavern 把整张卡 base64 后塞进 `chara` keyword。这个工具手写了 chunk 遍历（约 30 行），不依赖 Pillow——所以它也能查出 chunk 结构损坏的卡。

## Notes

- 只做结构和完整性校验，不评判写卡水平
- 零依赖，纯标准库

## License

MIT
