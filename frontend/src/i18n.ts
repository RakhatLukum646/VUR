import { useAppStore } from './store/useAppStore';
import type { Language } from './types';

type EasySignItem = {
  sign: string;
  meaning: string;
  cue: string;
  gif: string;
};

type ResourceSite = {
  href: string;
  title: string;
  subtitle: string;
  summary: string;
  logoSrc?: string;
};

type UiCopy = {
  interfaceLanguage: string;
  translationLanguage: string;
  status: {
    connected: string;
    connecting: string;
    error: string;
    disconnected: string;
    websocketActive: string;
    websocketInactive: string;
  };
  nav: {
    translator: string;
    resources: string;
    profile: string;
    admin: string;
    github: string;
    logout: string;
    backToTranslator: string;
    tagline: string;
  };
  controls: {
    start: string;
    stop: string;
    clear: string;
    signs: string;
    translating: string;
    tipLabel: string;
    tip: string;
  };
  camera: {
    retry: string;
    initializing: string;
    ready: string;
    active: string;
    inactive: string;
    resolution: string;
  };
  statusBar: {
    title: string;
    llmService: string;
    allReady: string;
    someDown: string;
    strong: string;
    warming: string;
    needsAdjustment: string;
    defaultGuidance: string;
  };
  panel: {
    title: string;
    currentDetection: string;
    classifierConfidence: string;
    noHand: string;
    highConfidence: string;
    moderateConfidence: string;
    lowConfidence: string;
    frameQuality: string;
    stability: string;
    bufferedSigns: string;
    detectedSigns: string;
    noSignsDetected: string;
    signsDetected: string;
    translatedSentence: string;
    voice: string;
    autoVoice: string;
    showFewerVoices: string;
    showAllVoices: string;
    showLess: string;
    showAll: string;
    reading: string;
    retranslateTitle: string;
    retranslating: string;
    retranslate: string;
    resume: string;
    pause: string;
    stopSpeaking: string;
    readAloud: string;
    stop: string;
    translationPlaceholder: string;
    recentHistory: string;
  };
  translator: {
    translateButton: string;
    howToUse: string;
    steps: string[];
    privacy: string;
    connectionFailed: string;
    translationStarted: string;
    translationStartedDetail: string;
    noSigns: string;
    noSignsDetail: string;
    offlineMode: string;
    offlineDetail: string;
    translationComplete: string;
    translationFailed: string;
    serviceError: string;
    unexpectedError: string;
    footerProject: string;
    sessionId: string;
  };
  easySigns: {
    title: string;
    intro: string;
    imageAltSuffix: string;
    items: EasySignItem[];
  };
  resources: {
    title: string;
    intro: string;
    videosTitle: string;
    videosIntro: string;
    courseTitle: string;
    arkTitle: string;
    arkIntro: string;
    sitesTitle: string;
    sitesIntro: string;
    openSite: string;
    youtubeMeta: string;
    lessons: string[];
    arkVideoTitle: string;
    sites: ResourceSite[];
  };
};

export const UI_LANGUAGES: { value: Language; label: string; shortLabel: string }[] = [
  { value: 'en', label: 'English', shortLabel: 'EN' },
  { value: 'ru', label: 'Русский', shortLabel: 'RU' },
  { value: 'kz', label: 'Қазақша', shortLabel: 'KZ' },
];

const easySignGifs = {
  hello: '/easy-signs/hello.gif?v=20260515-user',
  thankYou: '/easy-signs/thank_you.gif?v=20260515-user',
  yes: '/easy-signs/yes.gif?v=20260515-user',
  house: '/easy-signs/house.gif?v=20260515-user',
  please: '/easy-signs/please.gif?v=20260515-user',
};

const sharedResourceSites = {
  spreadTheSign: 'https://spreadthesign.ru/',
  surdo: 'https://surdo.media/',
  signlang: 'https://signlang.ru/studyrsl/lessons1-11/',
};

export const UI_COPY: Record<Language, UiCopy> = {
  en: {
    interfaceLanguage: 'Interface language',
    translationLanguage: 'Translation language',
    status: {
      connected: 'Connected',
      connecting: 'Connecting...',
      error: 'Error',
      disconnected: 'Disconnected',
      websocketActive: 'WebSocket active',
      websocketInactive: 'WebSocket inactive',
    },
    nav: {
      translator: 'Translator',
      resources: 'Resources',
      profile: 'Profile',
      admin: 'Admin',
      github: 'GitHub',
      logout: 'Logout',
      backToTranslator: 'Back to translator',
      tagline: 'Real-time sign language translation',
    },
    controls: {
      start: 'Start Translation',
      stop: 'Stop',
      clear: 'Clear',
      signs: 'signs',
      translating: 'Translating...',
      tipLabel: 'Tip:',
      tip: 'Position your hand clearly in front of the camera. The system recognizes Russian Sign Language gestures. Hold each sign for about one second, then pause between words.',
    },
    camera: {
      retry: 'Retry',
      initializing: 'Initializing camera...',
      ready: 'Camera ready',
      active: 'Camera active',
      inactive: 'Camera inactive',
      resolution: 'Resolution',
    },
    statusBar: {
      title: 'Service Status',
      llmService: 'LLM Service',
      allReady: 'All Services Ready',
      someDown: 'Some Services Down',
      strong: 'Recognition strong',
      warming: 'Recognition warming up',
      needsAdjustment: 'Recognition needs adjustment',
      defaultGuidance: 'Show one hand in the frame to start detection.',
    },
    panel: {
      title: 'Translation Panel',
      currentDetection: 'Current Detection',
      classifierConfidence: 'Classifier confidence',
      noHand: 'No hand detected yet.',
      highConfidence: 'High confidence. The hand shape looks consistent.',
      moderateConfidence: 'Moderate confidence. Hold the gesture a bit longer.',
      lowConfidence: 'Low confidence. Adjust framing, lighting, or hand shape.',
      frameQuality: 'Frame quality',
      stability: 'Stability',
      bufferedSigns: 'Buffered signs in current phrase',
      detectedSigns: 'Detected Signs',
      noSignsDetected: 'No signs detected yet...',
      signsDetected: 'signs detected',
      translatedSentence: 'Translated Sentence',
      voice: 'Voice',
      autoVoice: 'Auto voice',
      showFewerVoices: 'Show fewer voices',
      showAllVoices: 'Show all voices',
      showLess: 'Show less',
      showAll: 'Show all',
      reading: 'Reading',
      retranslateTitle: 'Re-translate last phrase with current language',
      retranslating: 'Translating...',
      retranslate: 'Re-translate',
      resume: 'Resume',
      pause: 'Pause',
      stopSpeaking: 'Stop speaking',
      readAloud: 'Read aloud',
      stop: 'Stop',
      translationPlaceholder: 'Translation will appear here when you complete a sign sequence...',
      recentHistory: 'Recent History',
    },
    translator: {
      translateButton: 'Translate Signs to Sentence',
      howToUse: 'How to Use',
      steps: [
        'Allow camera access when prompted',
        'Click "Start Translation" to begin',
        'Keep one hand centered, well lit, and large enough in the frame',
        'Perform RSL gestures. The model captures about one second per word, then recognizes it automatically',
        'Click "Translate Signs to Sentence" to get a grammatically correct translation via Gemini',
        'Click "Clear" to start a new session',
      ],
      privacy: 'Privacy note: camera frames are processed for live recognition and are not stored by the frontend.',
      connectionFailed: 'Connection failed',
      translationStarted: 'Translation started',
      translationStartedDetail: 'Make sign gestures in front of the camera.',
      noSigns: 'No signs detected',
      noSignsDetail: 'Make some gestures first before translating.',
      offlineMode: 'Offline mode',
      offlineDetail: 'Gemini API unavailable - showing raw sign sequence as fallback.',
      translationComplete: 'Translation complete',
      translationFailed: 'Translation failed',
      serviceError: 'Service error',
      unexpectedError: 'An unexpected error occurred.',
      footerProject: 'AITU Diploma Project - Team: Ulzhan, Vlad, Rakhat',
      sessionId: 'Session ID',
    },
    easySigns: {
      title: 'Top 5 Easy Signs',
      intro: 'Start with short, high-frequency signs that are easy to practice before using the live translator.',
      imageAltSuffix: 'sign preview',
      items: [
        { sign: 'Hello', meaning: 'A friendly greeting', cue: 'Open hand moves outward from the forehead.', gif: easySignGifs.hello },
        { sign: 'Thank you', meaning: 'Show gratitude', cue: 'Flat hand moves forward from the chin.', gif: easySignGifs.thankYou },
        { sign: 'Yes', meaning: 'Agree or confirm', cue: 'Closed hand nods up and down.', gif: easySignGifs.yes },
        { sign: 'House', meaning: 'A building or home', cue: 'Hands outline the roof and walls of a house.', gif: easySignGifs.house },
        { sign: 'Please', meaning: 'Make a polite request', cue: 'Flat hand circles gently on the chest.', gif: easySignGifs.please },
      ],
    },
    resources: {
      title: 'Resources and materials',
      intro: 'Dictionaries, articles, and videos for Russian Sign Language. Use these resources to practice vocabulary, compare explanations, and learn more about sign language culture.',
      videosTitle: 'Videos and lessons',
      videosIntro: 'Tutorials and playlists open on YouTube in a new tab.',
      courseTitle: 'Sign language course - Community of Families of Deafblind People',
      arkTitle: 'ARK MEDIA - video dictionary of signs',
      arkIntro: 'The channel contains playlists with sign vocabulary. The video below is a starting point; open the channel on YouTube to see the playlist section.',
      sitesTitle: 'Sites and references',
      sitesIntro: 'Each card includes the source, resource type, short description, and an external link.',
      openSite: 'Open site',
      youtubeMeta: 'YouTube - new tab',
      lessons: ['Lesson 1', 'Lesson 2', 'Lesson 3', 'Lesson 4', 'Lesson 5'],
      arkVideoTitle: 'ARK MEDIA video lesson',
      sites: [
        {
          href: sharedResourceSites.spreadTheSign,
          title: 'Spread The Sign (RU)',
          subtitle: 'spreadthesign.ru - RSL dictionary',
          summary: 'A visual sign dictionary with videos and descriptions. Useful for checking individual signs and comparing hand shapes before practicing in the translator.',
        },
        {
          href: sharedResourceSites.surdo,
          title: 'Surdo.media',
          subtitle: 'surdo.media - theory and practice',
          summary: 'Articles about Russian Sign Language, Deaf culture, communication, and the difference between sign language and signed Russian.',
        },
        {
          href: sharedResourceSites.signlang,
          title: 'Sign Language Linguistics Laboratory',
          subtitle: 'signlang.ru - study course',
          summary: 'A structured learning course with lessons and supporting materials. Good for moving from separate signs to a more systematic understanding.',
        },
      ],
    },
  },
  ru: {
    interfaceLanguage: 'Язык интерфейса',
    translationLanguage: 'Язык перевода',
    status: {
      connected: 'Подключено',
      connecting: 'Подключение...',
      error: 'Ошибка',
      disconnected: 'Отключено',
      websocketActive: 'WebSocket активен',
      websocketInactive: 'WebSocket неактивен',
    },
    nav: {
      translator: 'Переводчик',
      resources: 'Ресурсы',
      profile: 'Профиль',
      admin: 'Админ',
      github: 'GitHub',
      logout: 'Выйти',
      backToTranslator: 'К переводчику',
      tagline: 'Перевод жестового языка в реальном времени',
    },
    controls: {
      start: 'Начать перевод',
      stop: 'Стоп',
      clear: 'Очистить',
      signs: 'жестов',
      translating: 'Перевод...',
      tipLabel: 'Совет:',
      tip: 'Держите руку четко перед камерой. Система распознает жесты русского жестового языка. Показывайте жест около секунды и делайте паузу между словами.',
    },
    camera: {
      retry: 'Повторить',
      initializing: 'Инициализация камеры...',
      ready: 'Камера готова',
      active: 'Камера активна',
      inactive: 'Камера неактивна',
      resolution: 'Разрешение',
    },
    statusBar: {
      title: 'Статус сервисов',
      llmService: 'LLM-сервис',
      allReady: 'Все сервисы готовы',
      someDown: 'Некоторые сервисы недоступны',
      strong: 'Распознавание стабильное',
      warming: 'Распознавание настраивается',
      needsAdjustment: 'Нужно поправить кадр',
      defaultGuidance: 'Покажите одну руку в кадре, чтобы начать распознавание.',
    },
    panel: {
      title: 'Панель перевода',
      currentDetection: 'Текущее распознавание',
      classifierConfidence: 'Уверенность классификатора',
      noHand: 'Рука пока не обнаружена.',
      highConfidence: 'Высокая уверенность. Форма руки выглядит стабильно.',
      moderateConfidence: 'Средняя уверенность. Подержите жест немного дольше.',
      lowConfidence: 'Низкая уверенность. Поправьте кадр, свет или форму руки.',
      frameQuality: 'Качество кадра',
      stability: 'Стабильность',
      bufferedSigns: 'Жестов в текущей фразе',
      detectedSigns: 'Распознанные жесты',
      noSignsDetected: 'Жесты пока не распознаны...',
      signsDetected: 'жестов распознано',
      translatedSentence: 'Переведенное предложение',
      voice: 'Голос',
      autoVoice: 'Авто голос',
      showFewerVoices: 'Показать меньше голосов',
      showAllVoices: 'Показать все голоса',
      showLess: 'Меньше',
      showAll: 'Все',
      reading: 'Читает',
      retranslateTitle: 'Перевести последнюю фразу на текущий язык',
      retranslating: 'Перевод...',
      retranslate: 'Перевести заново',
      resume: 'Продолжить',
      pause: 'Пауза',
      stopSpeaking: 'Остановить озвучивание',
      readAloud: 'Озвучить',
      stop: 'Стоп',
      translationPlaceholder: 'Перевод появится здесь после завершения последовательности жестов...',
      recentHistory: 'Недавняя история',
    },
    translator: {
      translateButton: 'Перевести жесты в предложение',
      howToUse: 'Как пользоваться',
      steps: [
        'Разрешите доступ к камере',
        'Нажмите "Начать перевод"',
        'Держите одну руку по центру, в хорошем освещении и достаточно крупно',
        'Показывайте жесты РЖЯ. Модель берет около секунды на слово и распознает его автоматически',
        'Нажмите "Перевести жесты в предложение", чтобы получить грамотный перевод через Gemini',
        'Нажмите "Очистить", чтобы начать новую сессию',
      ],
      privacy: 'Приватность: кадры с камеры обрабатываются для распознавания в реальном времени и не сохраняются фронтендом.',
      connectionFailed: 'Ошибка подключения',
      translationStarted: 'Перевод запущен',
      translationStartedDetail: 'Показывайте жесты перед камерой.',
      noSigns: 'Жесты не найдены',
      noSignsDetail: 'Сначала покажите несколько жестов.',
      offlineMode: 'Офлайн-режим',
      offlineDetail: 'Gemini API недоступен - показана исходная последовательность жестов.',
      translationComplete: 'Перевод готов',
      translationFailed: 'Не удалось перевести',
      serviceError: 'Ошибка сервиса',
      unexpectedError: 'Произошла неожиданная ошибка.',
      footerProject: 'Дипломный проект AITU - команда: Ulzhan, Vlad, Rakhat',
      sessionId: 'ID сессии',
    },
    easySigns: {
      title: 'Топ-5 простых жестов',
      intro: 'Начните с коротких частых жестов, которые удобно отработать перед использованием переводчика.',
      imageAltSuffix: 'пример жеста',
      items: [
        { sign: 'Привет', meaning: 'Дружеское приветствие', cue: 'Открытая ладонь движется от лба наружу.', gif: easySignGifs.hello },
        { sign: 'Спасибо', meaning: 'Выразить благодарность', cue: 'Плоская ладонь движется вперед от подбородка.', gif: easySignGifs.thankYou },
        { sign: 'Да', meaning: 'Согласие или подтверждение', cue: 'Сжатая кисть кивает вверх-вниз.', gif: easySignGifs.yes },
        { sign: 'Дом', meaning: 'Здание или жилье', cue: 'Руки показывают крышу и стены дома.', gif: easySignGifs.house },
        { sign: 'Пожалуйста', meaning: 'Вежливая просьба', cue: 'Плоская ладонь мягко двигается кругом у груди.', gif: easySignGifs.please },
      ],
    },
    resources: {
      title: 'Ресурсы и материалы',
      intro: 'Словари, статьи и видео по русскому жестовому языку. Используйте эти материалы, чтобы тренировать лексику, сверять объяснения и лучше понимать культуру жестового языка.',
      videosTitle: 'Видео и уроки',
      videosIntro: 'Уроки и плейлисты открываются на YouTube в новой вкладке.',
      courseTitle: 'Курс жестового языка - Сообщество семей слепоглухих',
      arkTitle: 'ARK MEDIA - видео-словарь жестов',
      arkIntro: 'На канале есть плейлисты со словарем жестов. Видео ниже можно использовать как стартовую точку; на YouTube откройте канал и раздел плейлистов.',
      sitesTitle: 'Сайты и справочники',
      sitesIntro: 'В каждой карточке указаны источник, тип ресурса, короткое описание и внешняя ссылка.',
      openSite: 'Открыть сайт',
      youtubeMeta: 'YouTube - новая вкладка',
      lessons: ['Урок 1', 'Урок 2', 'Урок 3', 'Урок 4', 'Урок 5'],
      arkVideoTitle: 'Видео-урок ARK MEDIA',
      sites: [
        {
          href: sharedResourceSites.spreadTheSign,
          title: 'Spread The Sign (RU)',
          subtitle: 'spreadthesign.ru - словарь РЖЯ',
          summary: 'Визуальный словарь жестов с видео и описаниями. Полезен для проверки отдельных жестов и сравнения формы руки перед тренировкой в переводчике.',
        },
        {
          href: sharedResourceSites.surdo,
          title: 'Surdo.media',
          subtitle: 'surdo.media - теория и практика',
          summary: 'Статьи о русском жестовом языке, культуре глухих, коммуникации и отличии жестового языка от жестового русского.',
        },
        {
          href: sharedResourceSites.signlang,
          title: 'Лаборатория лингвистики жестового языка',
          subtitle: 'signlang.ru - учебный курс',
          summary: 'Структурированный учебный курс с уроками и дополнительными материалами. Подходит для перехода от отдельных жестов к системному пониманию.',
        },
      ],
    },
  },
  kz: {
    interfaceLanguage: 'Интерфейс тілі',
    translationLanguage: 'Аударма тілі',
    status: {
      connected: 'Қосылды',
      connecting: 'Қосылуда...',
      error: 'Қате',
      disconnected: 'Ажыратылды',
      websocketActive: 'WebSocket белсенді',
      websocketInactive: 'WebSocket белсенді емес',
    },
    nav: {
      translator: 'Аудармашы',
      resources: 'Ресурстар',
      profile: 'Профиль',
      admin: 'Админ',
      github: 'GitHub',
      logout: 'Шығу',
      backToTranslator: 'Аудармашыға қайту',
      tagline: 'Ым тілін нақты уақытта аудару',
    },
    controls: {
      start: 'Аударманы бастау',
      stop: 'Тоқтату',
      clear: 'Тазарту',
      signs: 'ым',
      translating: 'Аударылуда...',
      tipLabel: 'Кеңес:',
      tip: 'Қолыңызды камера алдында анық ұстаңыз. Жүйе орыс ым тілінің қимылдарын таниды. Әр ымды шамамен бір секунд көрсетіп, сөздер арасында кідіріс жасаңыз.',
    },
    camera: {
      retry: 'Қайталау',
      initializing: 'Камера іске қосылуда...',
      ready: 'Камера дайын',
      active: 'Камера белсенді',
      inactive: 'Камера белсенді емес',
      resolution: 'Ажыратымдылық',
    },
    statusBar: {
      title: 'Сервистер күйі',
      llmService: 'LLM сервисі',
      allReady: 'Барлық сервис дайын',
      someDown: 'Кейбір сервис қолжетімсіз',
      strong: 'Тану тұрақты',
      warming: 'Тану бапталуда',
      needsAdjustment: 'Кадрды түзету керек',
      defaultGuidance: 'Тануды бастау үшін бір қолды кадрда көрсетіңіз.',
    },
    panel: {
      title: 'Аударма панелі',
      currentDetection: 'Ағымдағы тану',
      classifierConfidence: 'Классификатор сенімділігі',
      noHand: 'Қол әлі анықталмады.',
      highConfidence: 'Сенімділік жоғары. Қол пішіні тұрақты көрінеді.',
      moderateConfidence: 'Сенімділік орташа. Ымды сәл ұзағырақ ұстаңыз.',
      lowConfidence: 'Сенімділік төмен. Кадрды, жарықты немесе қол пішінін түзетіңіз.',
      frameQuality: 'Кадр сапасы',
      stability: 'Тұрақтылық',
      bufferedSigns: 'Ағымдағы фразадағы ымдар',
      detectedSigns: 'Танылған ымдар',
      noSignsDetected: 'Әзірге ым танылмады...',
      signsDetected: 'ым танылды',
      translatedSentence: 'Аударылған сөйлем',
      voice: 'Дауыс',
      autoVoice: 'Авто дауыс',
      showFewerVoices: 'Дауыстарды аз көрсету',
      showAllVoices: 'Барлық дауысты көрсету',
      showLess: 'Аз көрсету',
      showAll: 'Барлығы',
      reading: 'Оқып тұр',
      retranslateTitle: 'Соңғы фразаны ағымдағы тілге қайта аудару',
      retranslating: 'Аударылуда...',
      retranslate: 'Қайта аудару',
      resume: 'Жалғастыру',
      pause: 'Пауза',
      stopSpeaking: 'Оқуды тоқтату',
      readAloud: 'Дауыстап оқу',
      stop: 'Тоқтату',
      translationPlaceholder: 'Ымдар тізбегі аяқталғаннан кейін аударма осында шығады...',
      recentHistory: 'Соңғы тарих',
    },
    translator: {
      translateButton: 'Ымдарды сөйлемге аудару',
      howToUse: 'Қолдану тәртібі',
      steps: [
        'Камераға рұқсат беріңіз',
        '"Аударманы бастау" батырмасын басыңыз',
        'Бір қолды кадр ортасында, жақсы жарықта және анық ұстаңыз',
        'РЖЯ ымдарын көрсетіңіз. Модель әр сөзге шамамен бір секунд алып, автоматты түрде таниды',
        '"Ымдарды сөйлемге аудару" батырмасын басып, Gemini арқылы дұрыс аударма алыңыз',
        '"Тазарту" батырмасымен жаңа сессия бастаңыз',
      ],
      privacy: 'Құпиялылық: камера кадрлары нақты уақыттағы тану үшін өңделеді және фронтендте сақталмайды.',
      connectionFailed: 'Қосылу қатесі',
      translationStarted: 'Аударма басталды',
      translationStartedDetail: 'Камера алдында ымдарды көрсетіңіз.',
      noSigns: 'Ым табылмады',
      noSignsDetail: 'Алдымен бірнеше ым көрсетіңіз.',
      offlineMode: 'Офлайн режим',
      offlineDetail: 'Gemini API қолжетімсіз - бастапқы ымдар тізбегі көрсетілді.',
      translationComplete: 'Аударма дайын',
      translationFailed: 'Аудару сәтсіз',
      serviceError: 'Сервис қатесі',
      unexpectedError: 'Күтпеген қате пайда болды.',
      footerProject: 'AITU дипломдық жобасы - команда: Ulzhan, Vlad, Rakhat',
      sessionId: 'Сессия ID',
    },
    easySigns: {
      title: 'Ең оңай 5 ым',
      intro: 'Тікелей аудармашыны қолданбас бұрын жиі кездесетін қысқа ымдардан бастаңыз.',
      imageAltSuffix: 'ым мысалы',
      items: [
        { sign: 'Сәлем', meaning: 'Достық амандасу', cue: 'Ашық алақан маңдайдан сыртқа қозғалады.', gif: easySignGifs.hello },
        { sign: 'Рақмет', meaning: 'Алғыс білдіру', cue: 'Жалпақ алақан иектен алға қозғалады.', gif: easySignGifs.thankYou },
        { sign: 'Иә', meaning: 'Келісу немесе растау', cue: 'Жұмылған қол жоғары-төмен бас изейді.', gif: easySignGifs.yes },
        { sign: 'Үй', meaning: 'Ғимарат немесе баспана', cue: 'Қолдар үйдің шатыры мен қабырғасын көрсетеді.', gif: easySignGifs.house },
        { sign: 'Өтінемін', meaning: 'Сыпайы өтініш', cue: 'Жалпақ алақан кеуде тұсында шеңбер жасайды.', gif: easySignGifs.please },
      ],
    },
    resources: {
      title: 'Ресурстар мен материалдар',
      intro: 'Орыс ым тілі бойынша сөздіктер, мақалалар және бейнелер. Бұл материалдар сөздік қорды жаттықтыруға, түсіндірмелерді салыстыруға және ым тілі мәдениетін жақсырақ түсінуге көмектеседі.',
      videosTitle: 'Бейнелер мен сабақтар',
      videosIntro: 'Сабақтар мен плейлистер YouTube-та жаңа қойындыда ашылады.',
      courseTitle: 'Ым тілі курсы - соқыр-керең адамдар отбасылары қауымдастығы',
      arkTitle: 'ARK MEDIA - ымдардың бейне-сөздігі',
      arkIntro: 'Каналдағы плейлистерде ым сөздігі бар. Төмендегі бейне бастапқы нүкте ретінде берілген; YouTube-та канал мен плейлисттер бөлімін ашыңыз.',
      sitesTitle: 'Сайттар мен анықтамалықтар',
      sitesIntro: 'Әр карточкада дереккөз, ресурс түрі, қысқа сипаттама және сыртқы сілтеме көрсетілген.',
      openSite: 'Сайтты ашу',
      youtubeMeta: 'YouTube - жаңа қойынды',
      lessons: ['Сабақ 1', 'Сабақ 2', 'Сабақ 3', 'Сабақ 4', 'Сабақ 5'],
      arkVideoTitle: 'ARK MEDIA бейне сабағы',
      sites: [
        {
          href: sharedResourceSites.spreadTheSign,
          title: 'Spread The Sign (RU)',
          subtitle: 'spreadthesign.ru - РЖЯ сөздігі',
          summary: 'Бейне мен сипаттамалары бар көрнекі ым сөздігі. Аудармашыда жаттықпас бұрын жеке ымдарды тексеруге және қол пішінін салыстыруға ыңғайлы.',
        },
        {
          href: sharedResourceSites.surdo,
          title: 'Surdo.media',
          subtitle: 'surdo.media - теория және тәжірибе',
          summary: 'Орыс ым тілі, естімейтіндер мәдениеті, коммуникация және ым тілі мен ымдық орыс тілінің айырмашылығы туралы мақалалар.',
        },
        {
          href: sharedResourceSites.signlang,
          title: 'Ым тілі лингвистикасы зертханасы',
          subtitle: 'signlang.ru - оқу курсы',
          summary: 'Сабақтары мен қосымша материалдары бар құрылымды оқу курсы. Жеке ымдардан жүйелі түсінуге көшуге көмектеседі.',
        },
      ],
    },
  },
};

export function useUiText() {
  const interfaceLanguage = useAppStore((state) => state.interfaceLanguage);
  return UI_COPY[interfaceLanguage] ?? UI_COPY.en;
}
