function initials(name) {
  return name.split(" ").map((part) => part[0]).slice(0, 2).join("").toUpperCase();
}

function Avatar({ user, size = 32, style }) {
  const dimension = { width: size, height: size, fontSize: size * 0.4 };

  if (user.avatar) {
    return (
      <img
        src={user.avatar}
        alt={user.name}
        className="avatar-img"
        style={{ ...dimension, ...style }}
      />
    );
  }

  return (
    <span className="sidebar-user-avatar" style={{ ...dimension, ...style }}>
      {initials(user.name)}
    </span>
  );
}

export default Avatar;
