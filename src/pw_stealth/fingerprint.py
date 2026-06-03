"""Desktop fingerprint values and opt-in profile patches for Playwright contexts."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Fingerprint:
    user_agent: str
    viewport: dict[str, int]
    locale: str
    timezone_id: str


@dataclass(frozen=True)
class FingerprintProfile:
    """Opt-in browser-surface overrides for authorized detection testing."""

    user_agent: str | None = None
    viewport: dict[str, int] | None = None
    locale: str | None = None
    timezone_id: str | None = None
    languages: tuple[str, ...] | None = None
    hardware_concurrency: int | None = None
    device_memory: int | float | None = None
    webgl_vendor: str | None = None
    webgl_renderer: str | None = None
    canvas_noise: bool = False
    canvas_noise_seed: int = 1

    def __post_init__(self) -> None:
        if self.viewport is not None:
            viewport = dict(self.viewport)
            if "width" not in viewport or "height" not in viewport:
                msg = "viewport must include width and height"
                raise ValueError(msg)
            object.__setattr__(self, "viewport", viewport)

        if self.languages is not None:
            languages = tuple(self.languages)
            if not languages:
                msg = "languages must not be empty"
                raise ValueError(msg)
            object.__setattr__(self, "languages", languages)

        if self.hardware_concurrency is not None and self.hardware_concurrency <= 0:
            msg = "hardware_concurrency must be positive"
            raise ValueError(msg)

        if self.device_memory is not None and self.device_memory <= 0:
            msg = "device_memory must be positive"
            raise ValueError(msg)

    @property
    def resolved_languages(self) -> tuple[str, ...] | None:
        if self.languages is not None:
            return self.languages
        if self.locale is None:
            return None
        return languages_from_locale(self.locale)


UA_POOL: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

VIEWPORTS: list[dict] = [
    {"width": 1366, "height": 768},
    {"width": 1366, "height": 900},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1920, "height": 1080},
]

LOCALES = ["en-US", "en-GB", "en-CA"]
TIMEZONES = ["America/New_York", "America/Chicago", "America/Los_Angeles", "Europe/London"]


def random_fingerprint(seed: int | None = None) -> Fingerprint:
    """Return a deterministic fingerprint when seed is provided."""

    rng = random.Random(seed)
    return Fingerprint(
        user_agent=rng.choice(UA_POOL),
        viewport=dict(rng.choice(VIEWPORTS)),
        locale=rng.choice(LOCALES),
        timezone_id=rng.choice(TIMEZONES),
    )


STEALTH_FINGERPRINT = random_fingerprint(seed=0)


def languages_from_locale(locale: str) -> tuple[str, ...]:
    """Return a browser-like languages tuple for a locale."""

    language = locale.split("-", maxsplit=1)[0]
    if language == locale:
        return (locale,)
    return (locale, language)


def fingerprint_context_options(
    fingerprint: Fingerprint | FingerprintProfile | None,
) -> dict[str, Any]:
    """Return Playwright context options represented by a fingerprint object."""

    if fingerprint is None:
        return {}

    if isinstance(fingerprint, Fingerprint):
        return {
            "user_agent": fingerprint.user_agent,
            "viewport": dict(fingerprint.viewport),
            "locale": fingerprint.locale,
            "timezone_id": fingerprint.timezone_id,
        }

    options: dict[str, Any] = {}
    if fingerprint.user_agent is not None:
        options["user_agent"] = fingerprint.user_agent
    if fingerprint.viewport is not None:
        options["viewport"] = dict(fingerprint.viewport)
    if fingerprint.locale is not None:
        options["locale"] = fingerprint.locale
    if fingerprint.timezone_id is not None:
        options["timezone_id"] = fingerprint.timezone_id
    return options


def fingerprint_init_script(fingerprint: Fingerprint | FingerprintProfile | None) -> str:
    """Build profile-specific init-script patches.

    Empty fields on FingerprintProfile are intentionally ignored. The base stealth script
    remains responsible for generic webdriver/plugin patches.
    """

    if fingerprint is None:
        return ""

    snippets: list[str] = []
    if isinstance(fingerprint, Fingerprint):
        snippets.extend(
            [
                _navigator_getter_script("language", fingerprint.locale),
                _navigator_getter_script(
                    "languages",
                    list(languages_from_locale(fingerprint.locale)),
                ),
                _timezone_script(fingerprint.timezone_id),
            ]
        )
        return "\n".join(snippets)

    languages = fingerprint.resolved_languages
    if fingerprint.locale is not None:
        snippets.append(_navigator_getter_script("language", fingerprint.locale))
    if languages is not None:
        snippets.append(_navigator_getter_script("languages", list(languages)))
    if fingerprint.timezone_id is not None:
        snippets.append(_timezone_script(fingerprint.timezone_id))
    if fingerprint.hardware_concurrency is not None:
        snippets.append(
            _navigator_getter_script(
                "hardwareConcurrency",
                fingerprint.hardware_concurrency,
            )
        )
    if fingerprint.device_memory is not None:
        snippets.append(_navigator_getter_script("deviceMemory", fingerprint.device_memory))
    if fingerprint.webgl_vendor is not None or fingerprint.webgl_renderer is not None:
        snippets.append(_webgl_script(fingerprint.webgl_vendor, fingerprint.webgl_renderer))
    if fingerprint.canvas_noise:
        snippets.append(_canvas_noise_script(fingerprint.canvas_noise_seed))

    return "\n".join(snippets)


def _js(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"))


def _navigator_getter_script(name: str, value: Any) -> str:
    return f"""
(() => {{
  const value = {_js(value)};
  const readValue = () => Array.isArray(value) ? value.slice() : value;
  const descriptor = {{ get: readValue, configurable: true }};
  try {{
    Object.defineProperty(Navigator.prototype, {_js(name)}, descriptor);
  }} catch (_) {{
    try {{
      Object.defineProperty(navigator, {_js(name)}, descriptor);
    }} catch (_) {{}}
  }}
}})();
""".strip()


def _timezone_script(timezone_id: str) -> str:
    return f"""
(() => {{
  const timezoneId = {_js(timezone_id)};
  if (typeof Intl === "undefined" || !Intl.DateTimeFormat) return;
  const originalResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
  Object.defineProperty(Intl.DateTimeFormat.prototype, "resolvedOptions", {{
    value: function(...args) {{
      const options = originalResolvedOptions.apply(this, args);
      try {{
        Object.defineProperty(options, "timeZone", {{
          value: timezoneId,
          configurable: true,
          enumerable: true
        }});
      }} catch (_) {{
        options.timeZone = timezoneId;
      }}
      return options;
    }},
    configurable: true,
    writable: true
  }});
}})();
""".strip()


def _webgl_script(webgl_vendor: str | None, webgl_renderer: str | None) -> str:
    vendor = _js(webgl_vendor)
    renderer = _js(webgl_renderer)
    return f"""
(() => {{
  const vendor = {vendor};
  const renderer = {renderer};
  const patch = (prototype) => {{
    if (!prototype || !prototype.getParameter) return;
    const originalGetParameter = prototype.getParameter;
    Object.defineProperty(prototype, "getParameter", {{
      value: function(parameter) {{
        if (parameter === 37445 && vendor !== null) return vendor;
        if (parameter === 37446 && renderer !== null) return renderer;
        return originalGetParameter.apply(this, arguments);
      }},
      configurable: true,
      writable: true
    }});
  }};
  patch(window.WebGLRenderingContext && window.WebGLRenderingContext.prototype);
  patch(window.WebGL2RenderingContext && window.WebGL2RenderingContext.prototype);
}})();
""".strip()


def _canvas_noise_script(seed: int) -> str:
    return f"""
(() => {{
  const seed = {int(seed)};
  const applyNoise = (imageData) => {{
    if (!imageData || !imageData.data || !imageData.data.length) return imageData;
    const data = imageData.data;
    const stride = Math.max(4, Math.floor(data.length / 997));
    const delta = (Math.abs(seed) % 3) + 1;
    for (let i = Math.abs(seed) % 4; i < data.length; i += stride) {{
      data[i] = (data[i] + delta) & 255;
    }}
    return imageData;
  }};

  if (typeof CanvasRenderingContext2D !== "undefined") {{
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    Object.defineProperty(CanvasRenderingContext2D.prototype, "getImageData", {{
      value: function(...args) {{
        return applyNoise(originalGetImageData.apply(this, args));
      }},
      configurable: true,
      writable: true
    }});
  }}

  if (typeof HTMLCanvasElement !== "undefined") {{
    const touchCanvas = (canvas) => {{
      try {{
        const context = canvas.getContext("2d");
        if (!context || !canvas.width || !canvas.height) return;
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        context.putImageData(imageData, 0, 0);
      }} catch (_) {{}}
    }};

    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    Object.defineProperty(HTMLCanvasElement.prototype, "toDataURL", {{
      value: function(...args) {{
        touchCanvas(this);
        return originalToDataURL.apply(this, args);
      }},
      configurable: true,
      writable: true
    }});

    const originalToBlob = HTMLCanvasElement.prototype.toBlob;
    if (originalToBlob) {{
      Object.defineProperty(HTMLCanvasElement.prototype, "toBlob", {{
        value: function(...args) {{
          touchCanvas(this);
          return originalToBlob.apply(this, args);
        }},
        configurable: true,
        writable: true
      }});
    }}
  }}
}})();
""".strip()
