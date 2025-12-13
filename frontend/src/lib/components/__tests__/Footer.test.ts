import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import Footer from '../Footer.svelte';

describe('Footer', () => {
	it('should render as a footer element', () => {
		const { container } = render(Footer);

		const footer = container.querySelector('footer');
		expect(footer).toBeInTheDocument();
	});

	it('should display copyright text', () => {
		render(Footer);

		const currentYear = new Date().getFullYear();
		expect(screen.getByText(new RegExp(`© ${currentYear}`, 'i'))).toBeInTheDocument();
	});

	it('should display the app name in copyright', () => {
		render(Footer);

		expect(screen.getByText(/ans/i)).toBeInTheDocument();
	});

	it('should render Privacy link', () => {
		render(Footer);

		const privacyLink = screen.getByRole('link', { name: /privacy/i });
		expect(privacyLink).toBeInTheDocument();
	});

	it('should render Terms link', () => {
		render(Footer);

		const termsLink = screen.getByRole('link', { name: /terms/i });
		expect(termsLink).toBeInTheDocument();
	});

	it('should render Contact link', () => {
		render(Footer);

		const contactLink = screen.getByRole('link', { name: /contact/i });
		expect(contactLink).toBeInTheDocument();
	});
});
