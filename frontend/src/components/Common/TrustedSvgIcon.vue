<script>
const ALLOWED_TAGS = new Set([
  'svg',
  'g',
  'path',
  'rect',
  'circle',
  'ellipse',
  'line',
  'polyline',
  'polygon',
  'title'
]);

const ALLOWED_ATTRIBUTES = new Set([
  'aria-hidden',
  'class',
  'clip-rule',
  'cx',
  'cy',
  'd',
  'fill',
  'fill-rule',
  'height',
  'points',
  'r',
  'rx',
  'ry',
  'stroke',
  'stroke-linecap',
  'stroke-linejoin',
  'stroke-width',
  'viewbox',
  'width',
  'x',
  'x1',
  'x2',
  'xmlns',
  'y',
  'y1',
  'y2'
]);

const URL_ATTRIBUTE_PATTERN = /url\s*\(|javascript:/i;

function sanitizeSvg(svg) {
  if (typeof svg !== 'string' || !svg.trim().startsWith('<svg')) return '';
  if (typeof window === 'undefined' || typeof DOMParser === 'undefined') return '';

  const documentSvg = new DOMParser().parseFromString(svg, 'image/svg+xml');
  const parserError = documentSvg.querySelector('parsererror');
  const root = documentSvg.documentElement;

  if (parserError || !root || root.tagName.toLowerCase() !== 'svg') return '';

  const nodes = [root, ...root.querySelectorAll('*')];

  for (const node of nodes) {
    const tagName = node.tagName.toLowerCase();
    if (!ALLOWED_TAGS.has(tagName)) {
      node.remove();
      continue;
    }

    for (const attribute of [...node.attributes]) {
      const attributeName = attribute.name;
      const normalizedName = attributeName.toLowerCase();
      const attributeValue = attribute.value ?? '';

      if (
        normalizedName.startsWith('on') ||
        normalizedName.includes(':') ||
        !ALLOWED_ATTRIBUTES.has(normalizedName) ||
        URL_ATTRIBUTE_PATTERN.test(attributeValue)
      ) {
        node.removeAttribute(attributeName);
      }
    }
  }

  root.setAttribute('aria-hidden', 'true');
  return root.outerHTML;
}

export default {
  name: 'TrustedSvgIcon',

  props: {
    svg: {
      type: String,
      default: ''
    }
  },

  computed: {
    safeSvg() {
      return sanitizeSvg(this.svg);
    }
  }
};
</script>

<template>
  <span class="trusted-svg-icon" aria-hidden="true" v-html="safeSvg"></span>
</template>

<style scoped>
.trusted-svg-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
}

.trusted-svg-icon:deep(svg) {
  width: 100%;
  height: 100%;
}
</style>
