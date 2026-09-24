// Opt-in archive of the two-team Cooperation -> Negligence sequence.
// Default play uses three-team Cooperation. Combined is unchanged.
export const negligenceEnabled=new URLSearchParams(location.search).get('negligence')==='1';
