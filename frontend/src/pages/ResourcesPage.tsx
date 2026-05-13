import type { ReactNode } from 'react';
import { useState } from 'react';
import { ExternalLink, PlayCircle } from 'lucide-react';

const YOUTUBE_LESSONS: { id: string; label: string }[] = [
  { id: 'FAkuz-g8S4g', label: 'Урок 1' },
  { id: 'EhZ7fXpuInQ', label: 'Урок 2' },
  { id: 'e6YaTJKUFcw', label: 'Урок 3' },
  { id: 'Dm338ycIZSE', label: 'Урок 4' },
  { id: 'JTdUH6TQjK4', label: 'Урок 5' },
];

/** Добавьте файлы в `frontend/public/resources-logos/` и укажите путь, например `/resources-logos/spreadthesign.png` — иначе показывается иконка сайта (favicon). */
type SiteEntry = {
  href: string;
  title: string;
  subtitle: string;
  summary: string;
  logoSrc?: string;
};

const SITE_LINKS: SiteEntry[] = [
  {
    href: 'https://spreadthesign.ru/',
    title: 'Spread The Sign (RU)',
    subtitle: 'spreadthesign.ru · словарь РЖЯ',
    summary:
      'Некоммерческий словарь русского жестового языка от студенческой команды ПИН-КОД: доступ к жестам после блокировки зарубежного сервиса на территории России. Удобно смотреть видео жестов и описания; для части лексики есть тренировка с камерой и распознаванием показанного жеста.',
  },
  {
    href: 'https://surdo.media/',
    title: 'Surdo.media',
    subtitle: 'surdo.media · теория и практика РЖЯ',
    summary:
      'Материалы о русском жестовом языке: история развития в России и в мире, роль РЖЯ в общении и отличие от «жестового русского». Подходит тем, кто хочет понять язык глубже, чем отдельные жесты — контекст культуры глухих и осмысленное общение.',
  },
  {
    href: 'https://signlang.ru/studyrsl/lessons1-11/',
    title: 'Лаборатория лингвистики ЖЯ',
    subtitle: 'signlang.ru · курс «studyrsl»',
    summary:
      'Структурированный учебный курс по РЖЯ: уроки с 1 по 11, материалы лаборатории лингвистики жестового языка. Можно проходить последовательно и сочетать с видеоуроками ниже и практикой в нашем переводчике.',
  },
];

function faviconForUrl(href: string): string {
  try {
    const host = new URL(href).hostname;
    return `https://www.google.com/s2/favicons?domain=${encodeURIComponent(host)}&sz=128`;
  } catch {
    return '';
  }
}

function SiteLogo({
  href,
  logoSrc,
  title,
}: {
  href: string;
  logoSrc?: string;
  title: string;
}) {
  const fallback = faviconForUrl(href);
  const [src, setSrc] = useState(logoSrc ?? fallback);

  return (
    <div className="shrink-0 flex h-14 w-14 items-center justify-center rounded-xl border border-gray-200/90 bg-white p-2 shadow-sm dark:border-gray-600 dark:bg-gray-800">
      {src ? (
        <img
          src={src}
          alt=""
          width={48}
          height={48}
          className="h-10 w-10 object-contain"
          loading="lazy"
          decoding="async"
          onError={() => {
            if (logoSrc && src === logoSrc && fallback) {
              setSrc(fallback);
              return;
            }
            setSrc('');
          }}
        />
      ) : (
        <ExternalLink className="h-7 w-7 text-indigo-400" aria-hidden />
      )}
      <span className="sr-only">{title}</span>
    </div>
  );
}

function SiteCard({ entry }: { entry: SiteEntry }) {
  const { href, title, subtitle, summary, logoSrc } = entry;

  return (
    <article className="flex h-full flex-col rounded-2xl border border-gray-200/80 bg-white/90 shadow-sm backdrop-blur dark:border-gray-700 dark:bg-gray-900/70">
      <div className="flex gap-4 border-b border-gray-100 p-5 dark:border-gray-700/80">
        <SiteLogo href={href} logoSrc={logoSrc} title={title} />
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-semibold leading-snug text-gray-900 dark:text-gray-100">
            {title}
          </h3>
          <p className="mt-1 text-xs font-medium uppercase tracking-wide text-indigo-600/90 dark:text-indigo-400/90">
            {subtitle}
          </p>
        </div>
      </div>
      <div className="flex flex-1 flex-col p-5 pt-4">
        <p className="text-sm leading-relaxed text-gray-600 dark:text-gray-300">{summary}</p>
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300"
        >
          <ExternalLink className="h-4 w-4 shrink-0" aria-hidden />
          Открыть сайт
        </a>
      </div>
    </article>
  );
}

function YouTubeLessonCard({ videoId, title }: { videoId: string; title: string }) {
  const href = `https://www.youtube.com/watch?v=${videoId}`;
  const thumb = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex flex-col overflow-hidden rounded-xl border border-gray-200/80 bg-white shadow-sm transition-all hover:border-indigo-300 hover:shadow-md dark:border-gray-700 dark:bg-gray-900/80 dark:hover:border-indigo-700"
    >
      <div className="relative aspect-video bg-gray-900">
        <img
          src={thumb}
          alt=""
          className="h-full w-full object-cover opacity-90 transition-opacity group-hover:opacity-100"
          loading="lazy"
        />
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <PlayCircle className="h-14 w-14 text-white opacity-90 drop-shadow-md transition-transform group-hover:scale-105" />
        </div>
      </div>
      <div className="flex items-start gap-2 p-3">
        <PlayCircle
          className="mt-0.5 h-4 w-4 shrink-0 text-indigo-600 dark:text-indigo-400"
          aria-hidden
        />
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{title}</p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">YouTube · новая вкладка</p>
        </div>
      </div>
    </a>
  );
}

export default function ResourcesPage() {
  const introSecondary: ReactNode = (
    <>
      Чтобы поставить свой логотип, положите PNG/WebP в{' '}
      <code className="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-xs dark:bg-gray-800">
        frontend/public/resources-logos/
      </code>{' '}
      и в коде страницы задайте поле <code className="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-xs dark:bg-gray-800">logoSrc</code> для нужного сайта.
    </>
  );

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-10">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100 sm:text-3xl">
          Ресурсы и материалы
        </h1>
        <p className="mt-3 max-w-3xl leading-relaxed text-gray-600 dark:text-gray-300">
          Словари, статьи и видео по русскому жестовому языку (РЖЯ). Ниже карточки сайтов в одном
          формате; тексты одной насыщенности, чтобы было проще сравнивать ресурсы.
        </p>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-gray-500 dark:text-gray-400">
          {introSecondary}
        </p>
      </div>

      <section className="mb-14" aria-labelledby="videos-heading">
        <h2
          id="videos-heading"
          className="mb-2 flex items-center gap-2 text-xl font-semibold text-gray-900 dark:text-gray-100"
        >
          <PlayCircle className="h-6 w-6 shrink-0 text-indigo-600 dark:text-indigo-400" aria-hidden />
          Видео и уроки
        </h2>
        <p className="mb-6 max-w-3xl text-sm text-gray-600 dark:text-gray-400">
          Туториалы и плейлисты открываются на YouTube в новой вкладке.
        </p>

        <h3 className="mb-4 text-base font-semibold text-gray-800 dark:text-gray-200">
          Курс жестового языка — канал «Сообщество Семей Слепоглухих»
        </h3>
        <div className="mb-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {YOUTUBE_LESSONS.map((item) => (
            <YouTubeLessonCard key={item.id} videoId={item.id} title={item.label} />
          ))}
        </div>

        <h3 className="mb-4 text-base font-semibold text-gray-800 dark:text-gray-200">
          ARK MEDIA — видео-словарь жестов
        </h3>
        <p className="mb-4 max-w-3xl text-sm text-gray-600 dark:text-gray-400">
          На канале — плейлисты со словарём жестов; ниже одна запись как входная точка (на YouTube
          откройте канал и раздел плейлистов).
        </p>
        <div className="max-w-md">
          <YouTubeLessonCard
            videoId="JTdUH6TQjK4"
            title="Видео на канале ARK MEDIA (словарь жестов)"
          />
        </div>
      </section>

      <section aria-labelledby="sites-heading">
        <h2
          id="sites-heading"
          className="mb-2 flex items-center gap-2 text-xl font-semibold text-gray-900 dark:text-gray-100"
        >
          <ExternalLink className="h-6 w-6 shrink-0 text-indigo-600 dark:text-indigo-400" aria-hidden />
          Сайты и справочники
        </h2>
        <p className="mb-6 max-w-3xl text-sm text-gray-600 dark:text-gray-400">
          Один формат карточки: логотип слева (или авто-иконка сайта), заголовок, краткий тип ресурса,
          текст на два–три предложения и ссылка.
        </p>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {SITE_LINKS.map((entry) => (
            <SiteCard key={entry.href} entry={entry} />
          ))}
        </div>
      </section>
    </main>
  );
}
