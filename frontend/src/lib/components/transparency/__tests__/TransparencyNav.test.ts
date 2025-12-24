/**
 * TransparencyNav Component Tests (TDD)
 *
 * Issue #85: Frontend: Public Transparency Pages
 * These tests are written FIRST before implementing the component.
 */

import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import TransparencyNav from '../TransparencyNav.svelte';

describe('TransparencyNav', () => {
	beforeEach(() => {
		// Reset locale to English for consistent testing
		locale.set('en');
	});

	it('should render navigation container', () => {
		render(TransparencyNav);

		const nav = screen.getByRole('navigation');
		expect(nav).toBeInTheDocument();
	});

	it('should render all transparency page links', () => {
		render(TransparencyNav);

		// All 7 transparency pages should be present
		expect(screen.getByText('Methodology')).toBeInTheDocument();
		expect(screen.getByText('Organization')).toBeInTheDocument();
		expect(screen.getByText('Our Team')).toBeInTheDocument();
		expect(screen.getByText('Funding')).toBeInTheDocument();
		expect(screen.getByText('Partnerships')).toBeInTheDocument();
		expect(screen.getByText('Corrections Policy')).toBeInTheDocument();
		expect(screen.getByText('Privacy Policy')).toBeInTheDocument();
	});

	it('should render links with correct href attributes', () => {
		render(TransparencyNav);

		// Check all links have correct hrefs
		expect(screen.getByRole('link', { name: 'Methodology' })).toHaveAttribute(
			'href',
			'/about/methodology'
		);
		expect(screen.getByRole('link', { name: 'Organization' })).toHaveAttribute(
			'href',
			'/about/organization'
		);
		expect(screen.getByRole('link', { name: 'Our Team' })).toHaveAttribute(
			'href',
			'/about/team'
		);
		expect(screen.getByRole('link', { name: 'Funding' })).toHaveAttribute(
			'href',
			'/about/funding'
		);
		expect(screen.getByRole('link', { name: 'Partnerships' })).toHaveAttribute(
			'href',
			'/about/partnerships'
		);
		expect(screen.getByRole('link', { name: 'Corrections Policy' })).toHaveAttribute(
			'href',
			'/about/corrections-policy'
		);
		expect(screen.getByRole('link', { name: 'Privacy Policy' })).toHaveAttribute(
			'href',
			'/about/privacy-policy'
		);
	});

	it('should highlight current page when currentSlug prop is provided', () => {
		render(TransparencyNav, { props: { currentSlug: 'methodology' } });

		const methodologyLink = screen.getByRole('link', { name: 'Methodology' });
		expect(methodologyLink).toHaveAttribute('aria-current', 'page');
	});

	it('should not highlight any page when currentSlug is not provided', () => {
		render(TransparencyNav);

		const links = screen.getAllByRole('link');
		links.forEach((link) => {
			expect(link).not.toHaveAttribute('aria-current', 'page');
		});
	});

	it('should have accessible navigation label', () => {
		render(TransparencyNav);

		const nav = screen.getByRole('navigation');
		expect(nav).toHaveAttribute('aria-label', 'Transparency');
	});

	it('should render navigation title', () => {
		render(TransparencyNav);

		// Should have a heading for the nav section
		expect(screen.getByRole('heading', { name: 'About Us' })).toBeInTheDocument();
	});
});
