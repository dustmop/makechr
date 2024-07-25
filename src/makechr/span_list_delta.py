def get_delta(newer, older):
  include = []
  exclude = []
  same = []
  merge = []
  split = []
  diff = []
  i = j = 0
  # Zip the older and newer lists, comparing the elements against each other.
  while i < len(newer) and j < len(older):
    n = newer[i]
    d = older[j]
    if n.fully_left(d):
      include.append(n)
      i += 1
      continue
    if n.fully_right(d):
      exclude.append(d)
      j += 1
      continue
    if n.same_as(d):
      same.append(d)
      i += 1
      j += 1
      continue
    # Some kind of overlap has occured.
    overlap_new = []
    overlap_old = []
    while i < len(newer) and j < len(older):
      n = newer[i]
      d = older[j]
      if not n.overlap(d):
        break
      if not n in overlap_new:
        overlap_new.append(n)
      if not d in overlap_old:
        overlap_old.append(d)
      if n.right > d.right:
        j += 1
        continue
      elif n.right < d.right:
        i += 1
        continue
      else: # must n.right == d.right:
        i += 1
        j += 1
        break
    if i < len(newer) and newer[i] in overlap_new:
      i += 1
    if j < len(older) and older[j] in overlap_old:
      j += 1
    if len(overlap_new) == 1:
      merge.append({'new': overlap_new, 'old': overlap_old})
    elif len(overlap_old) == 1:
      split.append({'new': overlap_new, 'old': overlap_old})
    else:
      diff.append({'new': overlap_new, 'old': overlap_old})
  while i < len(newer):
    n = newer[i]
    include.append(n)
    i += 1
  while j < len(older):
    d = older[j]
    exclude.append(d)
    j += 1
  result = {}
  if include:
    result['include'] = include
  if exclude:
    result['exclude'] = exclude
  if same:
    result['same'] = same
  if merge:
    result['merge'] = merge
  if split:
    result['split'] = split
  if diff:
    result['diff'] = diff
  return result
