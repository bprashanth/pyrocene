// Opt-in archive of the two-team Cooperation -> Negligence sequence.
// Default play uses three-team Cooperation. Combined is unchanged.
export const negligenceEnabled=new URLSearchParams(location.search).get('negligence')==='1';
// Resolve against this module, so direct-port and /stage4/ gateway URLs agree.
export const appURL=path=>new URL(path,import.meta.url).href;
