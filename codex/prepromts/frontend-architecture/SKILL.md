---
name: frontend-architecture
description: "Vue 3 Composition API архитектура: UI/composables/stores/domain/infra; паттерн A (DTO в store + доменная обёртка); keyed-store; контракт API/ошибок; деньги/телефон; антипаттерны."
---



\# Vue 3 Composition API — архитектурный skill (store / composable / domain / infra)



\## Цель

Строить фронтенд так, чтобы:

\- сложные данные были инкапсулированы (как на бэке: данные + поведение)

\- состояние было предсказуемым и отлаживаемым

\- UI не знал деталей API/форматов/правил (деньги, телефон, валидация)



\## Базовая модель слоёв

1\) UI (components)

\- разметка, события, отображение

\- минимум логики



2\) Feature logic (composables)

\- сценарии: submit формы, загрузка списка, обработка ошибок

\- реактивность Vue (ref/computed/watch)

\- glue: UI ↔ domain ↔ infra



3\) Domain (чистые модули + доменные классы)

\- правила, инварианты, вычисления, преобразования

\- Phone/Money/Cart/Filters/OrderDraft и т.п.

\- без зависимостей от Vue (предпочтительно)



4\) Infrastructure (API client)

\- HTTP, JSON, ошибки, auth/CSRF

\- единый формат ошибок и ответов



\## Два типа состояния

\- Client/UI state: локальные флаги/форма/вкладки/модалки

\- Server state: данные с бэка (кэш, refetch, инвалидация)



Рекомендация:

\- server state: TanStack Query (Vue Query)

\- client/ui state: component/composable/store



\## Когда использовать что

\### Pure functions (`export function`)

Использовать, если:

\- детерминированная логика без Vue

\- парсинг/форматирование/валидация/маппинг DTO



Примеры: parsePhone(), parseRubToKopeks(), normalizeName()



\### Composable

Использовать, если:

\- логика сценария + реактивность

\- состояние "на экземпляр" (каждый вызов создает новое состояние)



Примеры: usePaymentForm(), useModal(), usePagination()



\### Store (Pinia)

Использовать, если:

\- состояние нужно нескольким компонентам/роутам

\- должно жить долго (session/user/settings/кэш справочников)

\- нужен devtools/persist/SSR-предсказуемость



Store — singleton-контейнер, но может хранить много экземпляров данных (см. keyed-store).



\## Основная проблема: "сложные данные" во Vue

Решение: доменная сущность (класс) + DTO в store + composable-склейка.



\### Паттерн A (рекомендуемый): Store хранит DTO, домен — обёртка

Идея:

\- store хранит реактивный plain DTO (данные)

\- доменный класс читает DTO по ссылке и даёт методы (поведение)

\- composable отдаёт dto для v-model и draft для чтения/валидации/payload



Плюсы:

\- DTO сериализуем, понятен devtools, удобен для persist/SSR

\- доменная логика централизована и тестируема

\- UI меняет dto, а бизнес-правила живут в классе



\### Почему DTO и класс разделены

DTO:

\- форма данных, сериализация, реактивность, devtools

Класс:

\- поведение, инварианты, удобный интерфейс (validate(), toRequest())



Если хранить классы в store:

\- сложнее persist/SSR/отладка, возможны нюансы реактивности и сериализации



\## Пример: деньги и телефон

Правила:

\- деньги хранить/передавать как копейки (int) или как строку, но валидировать строго

\- телефон нормализовать в E.164



\## API контракт и ошибки

Нужно договориться на уровне API:

\- успех: { ok: true, redirect\_url, payment\_id }

\- ошибка валидации: { ok: false, code: "validation\_error", field\_errors: {...} }

\- ошибка сервера: { ok: false, code: "server\_error", message }



UI не должен угадывать формат ошибок.



\## Infra: единый API клиент

\- одно место для fetch/json/errors/csrf

\- не размазывать fetch по composables



\## Реализация паттерна A (один экземпляр)

\### Store DTO

```ts

import { defineStore } from 'pinia'

import { reactive } from 'vue'



export type PaymentDraftDTO = {

&nbsp; full\_name: string

&nbsp; phone: string | null

&nbsp; amount\_kopeks: number | null

}



export const usePaymentDraftStore = defineStore('paymentDraft', () => {

&nbsp; const dto = reactive<PaymentDraftDTO>({

&nbsp;   full\_name: '',

&nbsp;   phone: null,

&nbsp;   amount\_kopeks: null,

&nbsp; })

&nbsp; return { dto }

})

Domain class (обёртка над DTO)

ts

Копировать код

import type { PaymentDraftDTO } from '@/stores/paymentDraft'



export class PaymentDraft {

&nbsp; constructor(private dto: PaymentDraftDTO) {}



&nbsp; get fullName() {

&nbsp;   return this.dto.full\_name.trim().replace(/\\s+/g, ' ')

&nbsp; }



&nbsp; validate(): string | null {

&nbsp;   if (!this.fullName) return 'Введите ФИО'

&nbsp;   if (!this.dto.phone) return 'Некорректный телефон'

&nbsp;   if (!this.dto.amount\_kopeks || this.dto.amount\_kopeks <= 0) return 'Некорректная сумма'

&nbsp;   return null

&nbsp; }



&nbsp; toRequest() {

&nbsp;   return {

&nbsp;     payment: {

&nbsp;       full\_name: this.fullName,

&nbsp;       phone: this.dto.phone,

&nbsp;       amount\_kopeks: this.dto.amount\_kopeks,

&nbsp;     },

&nbsp;   }

&nbsp; }

}

```



Composable: dto для записи, draft для чтения/логики

ts

Копировать код

```ts

import { computed } from 'vue'

import { usePaymentDraftStore } from '@/stores/paymentDraft'

import { PaymentDraft } from '@/domain/PaymentDraft'



export function usePaymentDraft() {

&nbsp; const store = usePaymentDraftStore()

&nbsp; const draft = computed(() => new PaymentDraft(store.dto))

&nbsp; return { dto: store.dto, draft }

}

```

UI делает v-model по dto, а submit вызывает draft.validate()/draft.toRequest().



Один store — много экземпляров данных (ключевой ответ про singleton)

Store singleton не ограничивает одним объектом.

Храним коллекцию DTO по ключу: drafts\[key] -> DTO.



Keyed store

ts

Копировать код

```ts

import { defineStore } from 'pinia'

import { reactive } from 'vue'



export type PaymentDraftDTO = { full\_name: string; phone: string | null; amount\_kopeks: number | null }



function defaultDraft(): PaymentDraftDTO {

&nbsp; return { full\_name: '', phone: null, amount\_kopeks: null }

}



export const usePaymentDraftsStore = defineStore('paymentDrafts', () => {

&nbsp; const drafts = reactive<Record<string, PaymentDraftDTO>>({})



&nbsp; function ensure(key: string): PaymentDraftDTO {

&nbsp;   if (!drafts\[key]) drafts\[key] = defaultDraft()

&nbsp;   return drafts\[key]

&nbsp; }



&nbsp; function remove(key: string) {

&nbsp;   delete drafts\[key]

&nbsp; }



&nbsp; return { drafts, ensure, remove }

})

Composable на экземпляр (по ключу)

ts

Копировать код

```ts

import { PaymentDraft } from '@/domain/PaymentDraft'

import { usePaymentDraftsStore } from '@/stores/paymentDrafts'



export function usePaymentDraft(key: string) {

&nbsp; const store = usePaymentDraftsStore()

&nbsp; const dto = store.ensure(key)

&nbsp; const draft = new PaymentDraft(dto)

&nbsp; return { dto, draft, dispose: () => store.remove(key) }

}

```

Использование на разных страницах/роутах

ключ должен идентифицировать сущность: pay:${orderId} или draft:${userId}:${formId}



разные ключи => разные DTO => независимые формы одновременно



Антипаттерны (что не делать)

composable, который одновременно: UI state + форматирование + fetch + redirect (смешение слоёв)



хранить деньги как float без правила округления/копеек



размазывать fetch и обработку ошибок по всем компонентам



хранить в store тяжёлые несериализуемые объекты без необходимости



строить UI на предположениях о формате ошибок API



Практические чеклисты

Выбор места для кода

чистая логика без Vue? -> domain/pure functions



сценарий + реактивность? -> composable



общее состояние для разных частей приложения? -> store



HTTP/ошибки/CSRF? -> infra api client



Для “сложных типов”

DTO в store (reactive plain)



доменный класс (обертка, validate/toRequest/инварианты)



composable отдает dto + draft (и сценарии submit/load при необходимости)



Дополнительно (если нужно)

Server state: TanStack Query для query/mutation/кэша/инвалидации



Тестирование: домен тестируется без Vue; composable тестируется с моками api; UI отдельно



\## Domain class (обёртка над DTO)



```ts

import type { PaymentDraftDTO } from '@/stores/paymentDraft'



export class PaymentDraft {

&nbsp; constructor(private dto: PaymentDraftDTO) {}



&nbsp; get fullName() {

&nbsp;   return this.dto.full\_name.trim().replace(/\\s+/g, ' ')

&nbsp; }



&nbsp; validate(): string | null {

&nbsp;   if (!this.fullName) return 'Введите ФИО'

&nbsp;   if (!this.dto.phone) return 'Некорректный телефон'

&nbsp;   if (!this.dto.amount\_kopeks || this.dto.amount\_kopeks <= 0) return 'Некорректная сумма'

&nbsp;   return null

&nbsp; }



&nbsp; toRequest() {

&nbsp;   return {

&nbsp;     payment: {

&nbsp;       full\_name: this.fullName,

&nbsp;       phone: this.dto.phone,

&nbsp;       amount\_kopeks: this.dto.amount\_kopeks,

&nbsp;     },

&nbsp;   }

&nbsp; }

}

```



\## Composable: dto для записи, draft для логики



```ts

import { computed } from 'vue'

import { usePaymentDraftStore } from '@/stores/paymentDraft'

import { PaymentDraft } from '@/domain/PaymentDraft'



export function usePaymentDraft() {

&nbsp; const store = usePaymentDraftStore()

&nbsp; const draft = computed(() => new PaymentDraft(store.dto))

&nbsp; return { dto: store.dto, draft }

}

```



\## Один store — много экземпляров данных (keyed-store)



Использовать, когда нужно параллельно вести несколько независимых “черновиков” (разные страницы/роуты/виджеты).



\### Keyed store



```ts

import { defineStore } from 'pinia'

import { reactive } from 'vue'



export type PaymentDraftDTO = {

&nbsp; full\_name: string

&nbsp; phone: string | null

&nbsp; amount\_kopeks: number | null

}



function defaultDraft(): PaymentDraftDTO {

&nbsp; return { full\_name: '', phone: null, amount\_kopeks: null }

}



export const usePaymentDraftsStore = defineStore('paymentDrafts', () => {

&nbsp; const drafts = reactive<Record<string, PaymentDraftDTO>>({})



&nbsp; function ensure(key: string): PaymentDraftDTO {

&nbsp;   if (!drafts\[key]) drafts\[key] = defaultDraft()

&nbsp;   return drafts\[key]

&nbsp; }



&nbsp; function remove(key: string) {

&nbsp;   delete drafts\[key]

&nbsp; }



&nbsp; return { drafts, ensure, remove }

})

```



\### Composable на экземпляр (по ключу)



```ts

import { PaymentDraft } from '@/domain/PaymentDraft'

import { usePaymentDraftsStore } from '@/stores/paymentDrafts'



export function usePaymentDraftByKey(key: string) {

&nbsp; const store = usePaymentDraftsStore()

&nbsp; const dto = store.ensure(key)

&nbsp; const draft = new PaymentDraft(dto)

&nbsp; return { dto, draft, dispose: () => store.remove(key) }

}

```



Ключи:

\- `pay:${orderId}`

\- `draft:${userId}:${formId}`



Разные ключи => разные DTO => независимые формы одновременно.



\## API контракт и ошибки



\- успех: `{ ok: true, redirect\_url, payment\_id }`

\- ошибка валидации: `{ ok: false, code: "validation\_error", field\_errors: {...} }`

\- ошибка сервера: `{ ok: false, code: "server\_error", message }`



\## Деньги и телефон



\- деньги: хранить/передавать как `amount\_kopeks: number` (int) или валидируемую строку -> строго парсить

\- телефон: нормализовать в E.164



\## Антипаттерны



\- “толстый” composable: UI + форматирование + fetch + redirect в одном месте

\- деньги как float без правила округления/копеек

\- fetch и обработка ошибок размазаны по компонентам

\- store хранит тяжёлые несериализуемые объекты без необходимости

\- нет контракта ошибок API

