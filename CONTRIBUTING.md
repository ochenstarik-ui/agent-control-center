# Contribution policy

Проект находится на стадии спецификации.

## До утверждения v1

Разрешены только изменения требований, архитектуры, исследований, ADR и validation tooling. Реализация продукта блокирована до явного operator approval и G1 PASS.

## Правила изменений

1. Каждое функциональное требование получает стабильный ID и acceptance test ID.
2. Изменение security boundary, API, данных, retention или integration contract требует обновить traceability и соответствующий ADR/open question.
3. Источники для внешних API должны быть официальными, с датой проверки.
4. Нельзя коммитить credentials, tokens, private keys, session exports или реальные пользовательские данные.
5. Перед локальным commit спецификационных изменений: structural validation, secret scan, `git diff --cached --check` и independent peer review точного staged-кандидата. Термин G2 зарезервирован за implementation gate из `SPECIFICATION.md` §12.3.
6. Local commit не означает разрешение на push; публикация проходит отдельный pre-publish gate.
