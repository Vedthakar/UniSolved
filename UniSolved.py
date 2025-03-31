import streamlit as st

def main():
    st.set_page_config(page_title="unisolv'd", page_icon="💼", layout="wide")
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "About", "Services", "Contact"])
    
    if page == "Home":
        home()
    elif page == "About":
        about()
    elif page == "Services":
        services()
    elif page == "Contact":
        contact()

def home():
    # Custom CSS with animations
    st.markdown(
        """
        <style>
        /* Keyframes for fadeIn animation */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        /* Keyframes for bounce animation */
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {transform: translateY(0);} 
            40% {transform: translateY(-10px);} 
            60% {transform: translateY(-5px);} 
        }
        .hero {
            background-image: url('https://source.unsplash.com/1600x900/?modern,technology');
            background-size: cover;
            background-position: center;
            padding: 100px 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            animation: fadeIn 2s ease-out;
        }
        .hero-title {
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 0.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.6);
        }
        .hero-subtitle {
            font-size: 1.5em;
            margin-bottom: 1em;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.6);
        }
        .hero-btn {
            background-color: #ff4b4b;
            color: white;
            border: none;
            padding: 12px 30px;
            font-size: 1.2em;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s ease;
            animation: bounce 2s infinite;
        }
        .hero-btn:hover {
            background-color: #e04343;
        }
        .overview-img {
            border-radius: 10px;
            transition: transform 0.3s ease;
        }
        .overview-img:hover {
            transform: scale(1.05);
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Hero section with animated background and text
    hero_html = """
    <div class="hero">
        <div class="hero-title">Welcome to unisolv'd</div>
        <div class="hero-subtitle">Innovative Solutions for Modern Business</div>
        <button class="hero-btn" onclick="window.location.href='#about'">Learn More</button>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)
    
    # Overview section
    st.markdown("## Our Commitment to Excellence")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.image("https://source.unsplash.com/400x300/?innovation", use_container_width=True, caption="Innovation")
        st.markdown("**Innovation**")
        st.write("We continuously innovate to bring the best solutions.")
        
    with col2:
        st.image("https://source.unsplash.com/400x300/?strategy", use_container_width=True, caption="Strategy")
        st.markdown("**Strategy**")
        st.write("Our strategic approach ensures success in every project.")
        
    with col3:
        st.image("https://source.unsplash.com/400x300/?growth", use_container_width=True, caption="Growth")
        st.markdown("**Growth**")
        st.write("Empowering your business for long-term growth.")
    
    # Additional Info section (from your screenshot)
    st.markdown("## Additional Information")
    colA, colB, colC = st.columns(3)
    
    with colA:
        st.subheader("Values")
        st.markdown(
            """
            - Integrated to make it more user-friendly based on data from our student-based surveys  
            - Quick and efficient online services  
            - Optimized for university students by using primary data from them  
            - Affordable solutions for students  
            - Customized solutions for university clients & based on coding by university students
            """
        )
    
    
    with colB:
        st.subheader("Students")
        st.markdown(
            """
            - All undergraduate university students (ages 17-29)  
            - Parents (ages 26-60) helping their children in university  
            - Common problems reported at registrar's offices and other departments  
            - Professors can also use this website to reach out to students
            """
        )

def about():
    st.title("About unisolv'd")
    st.write("We are a team of professionals dedicated to delivering excellence. With years of experience, unisolv'd offers customized solutions for businesses of all sizes.")

def services():
    st.title("Our Services")
    services_list = ["Consulting", "Marketing", "Web Development", "Customer Support"]
    for service in services_list:
        st.write(f"- {service}")

def contact():
    st.title("Contact unisolv'd")
    st.write("Fill out the form below to get in touch with us.")
    name = st.text_input("Name")
    email = st.text_input("Email")
    message = st.text_area("Message")
    if st.button("Submit"):
        st.success("Thank you! We will get back to you soon.")

if __name__ == "__main__":
    main()
