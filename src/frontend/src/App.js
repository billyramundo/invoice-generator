import './App.css';
import React, {useState} from 'react'

function App() {
  const[formData, setFormData] = useState({
    url: '',
    name: '',
    company: '',
    address1: '',
    address2: '',
    phone: '',
  });

  const [isAnimating, setIsAnimating] = useState(false);

  const handleChange = (event) => {
    const {name, value} = event.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if(!formData.url.trim()){
      alert("A URL is required to generate an invoice")
      return;
    }
  
    const res = await fetch('/create_pdf', {
      method: 'POST',
      headers: {
        'Content-Type' : 'application/json'
      },
      body: JSON.stringify(formData),
    })
    
    if(!res.ok){
      const errorData = await res.json();
      throw new Error(errorData.error || "An unknown error occurred");
    }
    
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'completed-invoice.pdf';
    document.body.appendChild(a);
    a.click();
    a.remove();

    setFormData({
      url: '',
      name: '',
      company: '',
      address1: '',
      address2: '',
      phone: '',
    });
  };

  const handleButtonClick = () => {
    setIsAnimating(true);
    setTimeout(() => {
      setIsAnimating(false);
    }, 200);
  };
  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold text-center text-orange-500">
        Garage Invoice Generator
      </h1>
      <div className='border-b mt-4'></div>
      {<p className='text-black text-lg italic mb-4 mt-4 text-center'>
        Get a fully populated* PDF invoice for any truck on Garage by simply pasting the listing URL below!
        </p>}
      <form className="flex flex-col items-center mt-4" onSubmit={handleSubmit}>
        <div className="mb-4 w-full max-w-md">
        <label className="block text-gray-700 font-bold text-sm mb-2" htmlFor="urlTextBox">
          Item URL <span className="text-red-500">*</span> :
        </label>
          <input 
            id="urlTextBox"
            name="url"
            type="text" 
            placeholder="withgarage.com/listing/123456" 
            className="mb-2 p-2 border border-gray-300 rounded w-full"
            value={formData.url}
            onChange={handleChange}
          />
        </div>
        {<p className='text-black italic mb-4'>
          The below fields are not necessary, but the invoice will be incomplete without them.
          </p>}
        <div className="mb-4 flex space-x-4">
          <div className="flex flex-col">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="nameTextBox">
              Full Name:
            </label>
            <input 
              id="nameTextBox"
              name="name"
              type="text" 
              placeholder="John Smith" 
              className="p-2 border border-gray-300 rounded w-64" 
              value={formData.name}
              onChange={handleChange}
            />
          </div>
          <div className="flex flex-col">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="companyTextBox">
              Company Name:
            </label>
            <input 
              id="companyTextBox"
              name="company"
              type="text" 
              placeholder="FDNY" 
              className="p-2 border border-gray-300 rounded w-64" 
              value={formData.company}
              onChange={handleChange}
            />
          </div>
        </div>
        <div className="mb-4 flex space-x-4">
          <div className="flex flex-col">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="address1TextBox">
              Address Line 1:
            </label>
            <input 
              id="address1TextBox"
              name="address1"
              type="text" 
              placeholder="300 E 40th Street" 
              className="p-2 border border-gray-300 rounded w-64" 
              value={formData.address1}
              onChange={handleChange}
            />
          </div>
          <div className="flex flex-col">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="address2TextBox">
              Address Line 2:
            </label>
            <input 
              id="address2TextBox"
              name="address2"
              type="text" 
              placeholder="New York, NY 10016" 
              className="p-2 border border-gray-300 rounded w-64" 
              value={formData.address2}
              onChange={handleChange}
            />
          </div>
        </div>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="phoneTextBox">
            Phone Number:
          </label>
          <input 
            id="phoneTextBox"
            name="phone"
            type="text" 
            placeholder="999-999-9999" 
            className="p-2 border border-gray-300 rounded w-64"
            value={formData.phone}
            onChange={handleChange} 
          />
        </div>
        <button 
          type="submit" 
          className={`bg-orange-500 hover:bg-orange-600 text-white font-bold py-2 px-4 rounded mt-4 ${isAnimating ? 'animate-click' : ''}`}
          onClick={handleButtonClick}
        >
          Generate
        </button>
      </form>
      <div className='border-b mt-10'></div>
      {<p className='text-gray-400 italic mt-10 text-center text-xs'>
        *There may be certain details missing if they are not included by you or the listing
        </p>}
    </div>
  );
}

export default App;
