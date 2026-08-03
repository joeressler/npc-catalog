import {
  AfterViewInit,
  Directive,
  DoCheck,
  ElementRef,
  HostListener,
  OnDestroy,
  inject,
} from '@angular/core';

/** Grow a textarea to fit its content; min-height ~6rem, no manual resize. */
@Directive({
  selector: 'textarea[appAutosizeTextarea]',
  standalone: true,
})
export class AutosizeTextareaDirective implements AfterViewInit, DoCheck, OnDestroy {
  private readonly el = inject(ElementRef<HTMLTextAreaElement>);
  private resizeObserver: ResizeObserver | null = null;
  private lastValue = '';

  ngAfterViewInit(): void {
    const textarea = this.el.nativeElement;
    textarea.style.resize = 'none';
    textarea.style.overflow = 'hidden';
    textarea.style.minHeight = '6rem';
    this.lastValue = textarea.value;
    this.resize();

    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(textarea);
  }

  ngDoCheck(): void {
    const current = this.el.nativeElement.value;
    if (current !== this.lastValue) {
      this.lastValue = current;
      this.resize();
    }
  }

  ngOnDestroy(): void {
    this.resizeObserver?.disconnect();
  }

  @HostListener('input')
  onInput(): void {
    this.lastValue = this.el.nativeElement.value;
    this.resize();
  }

  /** Re-measure after programmatic value changes or mode switches. */
  refresh(): void {
    this.lastValue = this.el.nativeElement.value;
    this.resize();
  }

  private resize(): void {
    const textarea = this.el.nativeElement;
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  }
}
