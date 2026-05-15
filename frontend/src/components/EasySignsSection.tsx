import { Sparkles } from 'lucide-react';
import { useUiText } from '../i18n';

export function EasySignsSection() {
  const t = useUiText();

  return (
    <section
      aria-labelledby="easy-signs-heading"
      className="mt-8 rounded-2xl border border-emerald-100 bg-emerald-50/70 p-6 dark:border-emerald-900 dark:bg-emerald-950/30"
    >
      <div className="mb-5">
        <h2
          id="easy-signs-heading"
          className="flex items-center gap-2 text-xl font-semibold text-emerald-950 dark:text-emerald-100"
        >
          <Sparkles className="h-5 w-5 text-emerald-600 dark:text-emerald-300" aria-hidden />
          {t.easySigns.title}
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-emerald-900/80 dark:text-emerald-100/80">
          {t.easySigns.intro}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {t.easySigns.items.map((item) => (
          <article
            key={item.gif}
            className="overflow-hidden rounded-xl border border-white/80 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-900"
          >
            <div className="aspect-[4/3] bg-gray-100 dark:bg-gray-800">
              <img
                src={item.gif}
                alt={`${item.sign} ${t.easySigns.imageAltSuffix}`}
                className="h-full w-full object-cover"
                loading="lazy"
              />
            </div>
            <div className="p-4">
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                {item.sign}
              </h3>
              <p className="mt-1 text-sm font-medium text-emerald-700 dark:text-emerald-300">
                {item.meaning}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-gray-600 dark:text-gray-300">
                {item.cue}
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
