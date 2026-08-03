import { marked } from 'marked';
import DOMPurify from 'dompurify';

marked.setOptions({ breaks: true });

/** Convert Markdown source to sanitized HTML safe for [innerHTML]. */
export function renderMarkdown(source: string): string {
  if (!source?.trim()) {
    return '';
  }
  const raw = marked.parse(source, { async: false }) as string;
  return DOMPurify.sanitize(raw);
}
