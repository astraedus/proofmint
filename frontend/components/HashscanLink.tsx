interface Props {
  href: string;
  label: string;
  mono?: boolean;
}

export default function HashscanLink({ href, label, mono = true }: Props) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-flex items-center gap-1.5 text-[#00D4AA] hover:text-[#00efc0] transition-colors underline-offset-2 hover:underline ${
        mono ? "font-mono text-sm" : "text-sm font-medium"
      }`}
    >
      {label}
      <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
      </svg>
    </a>
  );
}
