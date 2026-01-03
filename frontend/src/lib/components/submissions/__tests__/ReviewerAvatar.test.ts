import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import ReviewerAvatar from '../ReviewerAvatar.svelte';

describe('ReviewerAvatar', () => {
	describe('Initials Generation', () => {
		it('should generate initials from full name', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'md' }
			});
			expect(container.textContent).toContain('JD');
		});

		it('should generate initials from single name', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'Madonna', size: 'md' }
			});
			expect(container.textContent).toContain('M');
		});

		it('should generate initials from three-word name', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'Mary Jane Watson', size: 'md' }
			});
			expect(container.textContent).toContain('MW');
		});

		it('should handle email addresses when name not provided', () => {
			const { container } = render(ReviewerAvatar, {
				props: { email: 'john.doe@example.com', size: 'md' }
			});
			expect(container.textContent).toContain('JD');
		});

		it('should prioritize name over email', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'Jane Smith', email: 'john.doe@example.com', size: 'md' }
			});
			expect(container.textContent).toContain('JS');
		});
	});

	describe('Size Variants', () => {
		it('should render small size with correct classes', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'sm' }
			});
			const avatar = container.querySelector('[data-testid="reviewer-avatar"]');
			expect(avatar?.className).toContain('w-6');
			expect(avatar?.className).toContain('h-6');
			expect(avatar?.className).toContain('text-xs');
		});

		it('should render medium size with correct classes', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'md' }
			});
			const avatar = container.querySelector('[data-testid="reviewer-avatar"]');
			expect(avatar?.className).toContain('w-8');
			expect(avatar?.className).toContain('h-8');
			expect(avatar?.className).toContain('text-sm');
		});

		it('should render large size with correct classes', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'lg' }
			});
			const avatar = container.querySelector('[data-testid="reviewer-avatar"]');
			expect(avatar?.className).toContain('w-10');
			expect(avatar?.className).toContain('h-10');
			expect(avatar?.className).toContain('text-base');
		});

		it('should default to medium size when not specified', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'John Doe' }
			});
			const avatar = container.querySelector('[data-testid="reviewer-avatar"]');
			expect(avatar?.className).toContain('w-8');
			expect(avatar?.className).toContain('h-8');
		});
	});

	describe('Color Generation', () => {
		it('should have circular design', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'md' }
			});
			const avatar = container.querySelector('[data-testid="reviewer-avatar"]');
			expect(avatar?.className).toContain('rounded-full');
		});

		it('should generate consistent colors for same name', () => {
			const { container: container1 } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'md' }
			});
			const { container: container2 } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'md' }
			});
			const avatar1 = container1.querySelector('[data-testid="reviewer-avatar"]');
			const avatar2 = container2.querySelector('[data-testid="reviewer-avatar"]');

			// Both should have the same background color
			expect(avatar1?.getAttribute('style')).toBe(avatar2?.getAttribute('style'));
		});

		it('should generate different colors for different names', () => {
			const { container: container1 } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'md' }
			});
			const { container: container2 } = render(ReviewerAvatar, {
				props: { name: 'Jane Smith', size: 'md' }
			});
			const avatar1 = container1.querySelector('[data-testid="reviewer-avatar"]');
			const avatar2 = container2.querySelector('[data-testid="reviewer-avatar"]');

			// Should have different background colors
			expect(avatar1?.getAttribute('style')).not.toBe(avatar2?.getAttribute('style'));
		});

		it('should have white text color', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'md' }
			});
			const avatar = container.querySelector('[data-testid="reviewer-avatar"]');
			expect(avatar?.className).toContain('text-white');
		});
	});

	describe('Tooltip', () => {
		it('should display full name in title attribute', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'md' }
			});
			const avatar = container.querySelector('[data-testid="reviewer-avatar"]');
			expect(avatar?.getAttribute('title')).toBe('John Doe');
		});

		it('should display email in title when name not provided', () => {
			const { container } = render(ReviewerAvatar, {
				props: { email: 'john.doe@example.com', size: 'md' }
			});
			const avatar = container.querySelector('[data-testid="reviewer-avatar"]');
			expect(avatar?.getAttribute('title')).toBe('john.doe@example.com');
		});
	});

	describe('Accessibility', () => {
		it('should have proper aria-label', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'md' }
			});
			const avatar = container.querySelector('[data-testid="reviewer-avatar"]');
			expect(avatar?.getAttribute('aria-label')).toBe('Reviewer: John Doe');
		});

		it('should have role="img" for screen readers', () => {
			const { container } = render(ReviewerAvatar, {
				props: { name: 'John Doe', size: 'md' }
			});
			const avatar = container.querySelector('[data-testid="reviewer-avatar"]');
			expect(avatar?.getAttribute('role')).toBe('img');
		});
	});
});
