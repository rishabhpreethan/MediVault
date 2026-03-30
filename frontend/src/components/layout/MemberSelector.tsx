import { useFamilyMembers, useActiveMember, useSetActiveMember } from '../../hooks/useFamily'

export function MemberSelector() {
  const { data: members = [] } = useFamilyMembers()
  const activeMemberId = useActiveMember()
  const setActiveMember = useSetActiveMember()

  if (members.length <= 1) return null

  return (
    <select
      className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white min-h-[44px]"
      value={activeMemberId ?? ''}
      onChange={(e) => setActiveMember(e.target.value)}
      aria-label="Select family member"
    >
      {members.map((m) => (
        <option key={m.member_id} value={m.member_id}>
          {m.full_name} {m.is_self ? '(You)' : ''}
        </option>
      ))}
    </select>
  )
}
