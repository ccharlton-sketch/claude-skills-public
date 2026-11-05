// Small line icons (24px grid, 1.75 stroke), drawn inline so the site has no icon dependency.
type P = { className?: string };
const base = { width: 24, height: 24, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.75, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };

export const ArrowUpRight = ({ className }: P) => (<svg {...base} className={className}><path d="M7 17 17 7M8 7h9v9" /></svg>);
export const Calendar = ({ className }: P) => (<svg {...base} className={className}><rect x="3.5" y="5" width="17" height="15" rx="2.5" /><path d="M3.5 10h17M8 3v4M16 3v4" /></svg>);
export const Users = ({ className }: P) => (<svg {...base} className={className}><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.2a6.5 6.5 0 0 1 3.5 5.8" /></svg>);
export const Layers = ({ className }: P) => (<svg {...base} className={className}><path d="m12 3 9 5-9 5-9-5 9-5Z" /><path d="m3 13 9 5 9-5" /></svg>);
export const Flag = ({ className }: P) => (<svg {...base} className={className}><path d="M5 21V4M5 4h11l-2 4 2 4H5" /></svg>);
export const FileText = ({ className }: P) => (<svg {...base} className={className}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z" /><path d="M14 3v5h5M9 13h6M9 17h6" /></svg>);
export const Network = ({ className }: P) => (<svg {...base} className={className}><rect x="9" y="3" width="6" height="5" rx="1.2" /><rect x="3" y="16" width="6" height="5" rx="1.2" /><rect x="15" y="16" width="6" height="5" rx="1.2" /><path d="M12 8v4M6 16v-2h12v2" /></svg>);
export const Briefcase = ({ className }: P) => (<svg {...base} className={className}><rect x="3" y="7" width="18" height="13" rx="2.5" /><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18" /></svg>);
