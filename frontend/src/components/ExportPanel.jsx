import { useState, useEffect } from 'react'

function ExportPanel({ apiUrl }) {
  const [skills, setSkills] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedSkill, setSelectedSkill] = useState(null)

  useEffect(() => {
    // Fetch skills from API
    fetch(`${apiUrl}/api/skills`)
      .then(res => res.json())
      .then(data => {
        setSkills(data.skills || [])
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to fetch skills:', err)
        setLoading(false)
      })
  }, [apiUrl])

  const viewSkillDetails = (skillId) => {
    fetch(`${apiUrl}/api/skills?id=${skillId}`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.skill) {
          setSelectedSkill(data.skill)
        }
      })
      .catch(err => console.error('Failed to fetch skill details:', err))
  }

  return (
    <div className="export-panel">
      <h2>Skills Browser</h2>

      {loading ? (
        <div className="info-message">
          ⏳ Loading skills...
        </div>
      ) : (
        <div className="export-options">
          <h3>Available Analysis Skills</h3>
          <p style={{ marginBottom: '1.5rem', color: '#666' }}>
            Browse the built-in skills available for code analysis
          </p>

          <div className="format-cards">
            {skills.map((skill) => (
              <div key={skill.id} className="format-card">
                <h4>{skill.name}</h4>
                <div style={{
                  display: 'inline-block',
                  padding: '0.25rem 0.5rem',
                  background: '#e3f2fd',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  marginBottom: '0.5rem'
                }}>
                  {skill.category}
                </div>
                <p style={{ fontSize: '0.9rem', margin: '0.5rem 0' }}>
                  {skill.description}
                </p>
                <button
                  className="btn btn-secondary"
                  onClick={() => viewSkillDetails(skill.id)}
                  style={{ marginTop: '0.5rem' }}
                >
                  View Details
                </button>
              </div>
            ))}
          </div>

          {selectedSkill && (
            <div className="audit-preview" style={{ marginTop: '2rem' }}>
              <h3>{selectedSkill.name}</h3>
              <div className="preview-stats">
                <p><strong>ID:</strong> {selectedSkill.id}</p>
                <p><strong>Category:</strong> {selectedSkill.category}</p>
                <p><strong>Description:</strong> {selectedSkill.description}</p>
                {selectedSkill.enabled !== undefined && (
                  <p><strong>Status:</strong> {selectedSkill.enabled ? '✅ Enabled' : '❌ Disabled'}</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ExportPanel
